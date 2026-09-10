import json
import os
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

import httpx
from openai import OpenAI

from .types import SymbolManifest, InferenceResult, RepairPlan, RepairAction

class ContextBrain:
    def __init__(
        self,
        api_key: str | None,
        base_url: str = None,
        model: str = "gemini-2.0-flash-exp",
        provider: str = "openai",
        opencode_bin: str = "opencode",
        opencode_dir: str | None = None,
    ):
        self.provider = (provider or "openai").lower()
        self.api_key = api_key
        self.model = model
        self.opencode_bin = opencode_bin or "opencode"
        self.opencode_dir = opencode_dir
        self._proxy_url = self._detect_proxy_url()
        self._solidity_rules = (
            "[Solidity Generation Rules]\n"
            "1. Definition Completeness:\n"
            "   - If code references a nested struct (Contract.Struct), define that struct inside the contract.\n"
            "   - If code uses 'revert CustomError()', declare 'error CustomError();' within the contract.\n"
            "2. Scope Management:\n"
            "   - Do not leave orphan types. Every type in signatures must be defined.\n"
            "3. Shadowing Prevention:\n"
            "   - If a function argument would shadow a state variable with the same name, prefix the argument with an underscore.\n"
        )

        if self.provider == "opencode":
            self._clients = []
            self.client = None
            return

        # Prefer explicit base_url(s), but keep deterministic fallbacks so the LLM can still be used
        # when one compatible endpoint is temporarily unavailable.
        default_fallbacks = []
        base_urls = []
        if base_url:
            if isinstance(base_url, str) and "," in base_url:
                base_urls.extend([u.strip() for u in base_url.split(",") if u.strip()])
            else:
                base_urls.append(base_url)
        for fallback in default_fallbacks:
            if fallback not in base_urls:
                base_urls.append(fallback)

        transport = httpx.HTTPTransport(retries=3)
        self._clients = []
        proxy_url = self._proxy_url

        client_variants = []
        env_kwargs = {
            'timeout': 180.0,
            'trust_env': True,
            'transport': transport,
        }
        client_variants.append(env_kwargs)
        if proxy_url:
            proxy_kwargs = {
                'timeout': 180.0,
                'trust_env': True,
                'transport': httpx.HTTPTransport(retries=3),
            }
            client_variants.append(proxy_kwargs)

        for url in base_urls:
            for client_kwargs in client_variants:
                try:
                    client = OpenAI(
                        api_key=api_key,
                        base_url=url,
                        timeout=180.0,
                        http_client=httpx.Client(**client_kwargs),
                    )
                    self._clients.append((url, client))
                    break
                except Exception as exc:
                    print(f"[WARN] Failed to initialize OpenAI client for {url} with proxy={'proxy' in client_kwargs}: {exc}")
                    continue
        if not self._clients:
            raise RuntimeError("Failed to initialize any OpenAI-compatible client")

        self.client = self._clients[0][1]

    def infer(self, manifest: SymbolManifest) -> InferenceResult:
        """三步推理：1. 函数归位 2. Library 补全 3. 检测缺失接口"""
        result = InferenceResult()
        
        # 任务 A: 函数归位 (Re-homing)
        if manifest.orphans and manifest.contracts:
            prompt_rehome = self._build_rehome_prompt(manifest)
            response_rehome = self._call_llm(prompt_rehome)
            try:
                cleaned_json = response_rehome.strip()
                if cleaned_json.startswith('```json'):
                    cleaned_json = cleaned_json[7:]
                if cleaned_json.endswith('```'):
                    cleaned_json = cleaned_json[:-3]
                result.rehoming_map = json.loads(cleaned_json.strip())
            except Exception as e:
                print(f"Error parsing Re-homing JSON: {e}")

        # 任务 B, C, D: Library, Interfaces, Mocks 的并发处理
        FORGE_STD_LIBS = {'StdStyle', 'console', 'safeconsole', 'StdAssertions', 'Vm', 'StdCheats', 'Test'}
        GENERATE_LIBS = set()

        def fetch_mock_lib(lib_name, related_orphans, prompt_mock):
            mock_code = self._call_llm_text(prompt_mock)
            return ('lib', lib_name, mock_code, related_orphans)

        def fetch_batch_code(batch_id, prompt):
            code = self._call_llm_text(prompt)
            # Retry up to 2 more times if content is invalid
            for attempt in range(2):
                if self._is_valid_solidity_content(code):
                    break
                print(f"    [WARN] Batch '{batch_id}' returned invalid content (attempt {attempt+1}), retrying...")
                code = self._call_llm_text(prompt)
            else:
                print(f"    [WARN] Batch '{batch_id}' still invalid after retries, using empty placeholder")
                code = f"contract {batch_id} {{}}"
            return ('batch', batch_id, code, None)

        futures = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            # 任务 B
            if manifest.libraries:
                for lib in manifest.libraries:
                    if lib.name in FORGE_STD_LIBS:
                        continue
                    if lib.name in GENERATE_LIBS:
                        related_orphans = []
                        for o in manifest.orphans:
                            if lib.name.lower() in o.name.lower():
                                related_orphans.append(o)
                            elif lib.name == 'Address' and (o.name.startswith('function') or 'verifyCallResult' in o.name or o.name == '_revert'):
                                related_orphans.append(o)
                        prompt_mock = self._build_mock_prompt(lib.name, related_orphans if related_orphans else manifest.orphans)
                        futures.append(executor.submit(fetch_mock_lib, lib.name, related_orphans, prompt_mock))
                    else:
                        code_without_comments = lib.code.replace('/*', '').replace('*/', '').replace('//', '').strip()
                        is_empty = len(code_without_comments.replace(f'library {lib.name}', '').replace('{', '').replace('}', '').strip()) < 10
                        if not is_empty and '/* stdlib: collapsed */' not in lib.code:
                            result.mock_libraries[lib.name] = lib.code
            
            # 任务 C
            missing_interfaces = self._detect_missing_interfaces(manifest)
            if missing_interfaces:
                batch_size = 3
                for i in range(0, len(missing_interfaces), batch_size):
                    batch = missing_interfaces[i:i+batch_size]
                    prompt = self._build_interfaces_prompt(batch, manifest)
                    futures.append(executor.submit(fetch_batch_code, f"_InterfaceBatch_{i}", prompt))
            
            # 任务 D
            missing_mocks = self._detect_missing_mocks(manifest)
            if missing_mocks:
                batch_size = 3
                for i in range(0, len(missing_mocks), batch_size):
                    batch = missing_mocks[i:i+batch_size]
                    prompt = self._build_mock_contracts_prompt(batch, manifest)
                    futures.append(executor.submit(fetch_batch_code, f"_MockBatch_{i}", prompt))
            
            for future in as_completed(futures):
                try:
                    task_type, key, code, related_orphans = future.result()
                    result.mock_libraries[key] = code
                    if task_type == 'lib' and related_orphans:
                        for orphan in related_orphans:
                            if orphan.name in result.rehoming_map:
                                del result.rehoming_map[orphan.name]
                except Exception as e:
                    print(f"Error in concurrent task: {e}")

            # Second validation pass: replace any remaining invalid content with placeholders
            for key in list(result.mock_libraries.keys()):
                code = result.mock_libraries[key]
                if not self._is_valid_solidity_content(code):
                    print(f"    [WARN] Final validation: '{key}' has invalid content, replacing with placeholder")
                    if key.startswith('_InterfaceBatch') or key.startswith('_MockBatch'):
                        result.mock_libraries[key] = f"contract {key} {{}}"
                    else:
                        import re
                        # Try to extract a name
                        name_match = re.search(r'^library\s+(\w+)', code) or re.search(r'^contract\s+(\w+)', code) or re.search(r'^interface\s+(\w+)', code)
                        name = name_match.group(1) if name_match else key
                        result.mock_libraries[key] = f"contract {name} {{}}"

        # 任务 E: 检测并生成缺失的 error 定义 (本地执行)
        missing_errors = self._detect_missing_errors(manifest)
        if missing_errors:
            error_code = self._generate_error_definitions(missing_errors)
            result.mock_libraries['_ErrorDefinitions'] = error_code
        
        return result

    def _build_rehome_prompt(self, manifest: SymbolManifest) -> str:
        orphans_info = [{"name": o.name, "used_vars": list(set(o.used_identifiers)), "calls": o.call_expressions, "members": o.member_accesses, "returns": o.return_contexts} for o in manifest.orphans]
        contracts_info = [{"name": name, "state_vars": c.state_variables} for name, c in manifest.contracts.items()]
        
        return f"""
        You are a Solidity Static Analyzer.
        
        Task: Map "Orphan Functions" to their parent "Contracts" based on variable usage.
        
        Orphans: {json.dumps(orphans_info)}
        Available Contracts: {json.dumps(contracts_info)}
        
        Rules:
        1. If an orphan uses a variable that exists in a contract's state variables, it belongs there.
        2. If function name starts with 'test', it likely belongs to the contract named 'PoC' or 'Test'.
        3. If function starts with 'setMock', it belongs to a Mock contract.
        
        Output JSON Format ONLY:
        {{ "function_name": "ContractName", ... }}
        """

    def _build_mock_prompt(self, lib_name: str, orphans) -> str:
        context_snippets = [o.code for o in orphans if lib_name in o.code][:3]
        
        return f"""
        Generate a COMPLETE Solidity Library named '{lib_name}'.
        Goal: Create a Mock/Stub implementation to make the code compile.

        Context usages:
        {chr(10).join(context_snippets)}

        {self._solidity_rules}

        Requirements:
        1. Implement ALL functions inferred from usage.
        2. Preserve any required nested types in the correct owner scope.
        3. Do not invent additional public symbols unless strictly necessary.
        4. Output ONLY the solidity code block.
        """
    
    def _detect_missing_interfaces(self, manifest: SymbolManifest) -> list:
        """Return missing interface candidates from direct usage only."""
        import re
        from .symbol_table import build_symbol_table

        candidates = set()
        all_code = []
        for g_type in manifest.global_types:
            all_code.append(g_type)
        for contract in manifest.contracts.values():
            all_code.append(contract.code)
        for orphan in manifest.orphans:
            all_code.append(orphan.code)
        combined_code = '\n'.join(all_code)

        symbol_table = build_symbol_table(combined_code)
        defined_types = symbol_table.all_names()
        defined_types |= set(getattr(manifest.symbols, 'all_identifiers', set()))

        direct_usage_patterns = [
            r'new\s+(I[A-Z][A-Za-z0-9_]*)\s*\(',
            r'\b(I[A-Z][A-Za-z0-9_]*)\s*\(',
            r'\b(I[A-Z][A-Za-z0-9_]*)\.[A-Za-z_][A-Za-z0-9_]*\s*\(',
            r'\b(I[A-Z][A-Za-z0-9_]*)\s+memory\s+\w+',
            r'\b(I[A-Z][A-Za-z0-9_]*)\s+storage\s+\w+',
            r'\b(I[A-Z][A-Za-z0-9_]*)\s+calldata\s+\w+',
            r'\b(I[A-Z][A-Za-z0-9_]*)\s+\w+\s*(?:;|=|,|\))',
        ]
        for pattern in direct_usage_patterns:
            candidates.update(re.findall(pattern, combined_code))

        for orphan in manifest.orphans:
            for call in getattr(orphan, 'call_expressions', []):
                m = re.search(r'\b(I[A-Z][A-Za-z0-9_]*)\b', call)
                if m:
                    candidates.add(m.group(1))
            for member_access in getattr(orphan, 'member_accesses', []):
                m = re.match(r'(I[A-Z][A-Za-z0-9_]*)\.', member_access)
                if m:
                    candidates.add(m.group(1))

        builtins = {'String', 'Bytes', 'Address', 'Uint', 'Int', 'Bool', 'Test',
                    'Clone', 'PoC', 'AddressType', 'Math',
                    'Call', 'StaticCall', 'DelegateCall', 'Currency'}
        missing = [c for c in sorted(candidates) if c not in defined_types and c not in builtins and c.startswith('I')]
        return missing

    def _infer_arg_type(self, token: str) -> str:
        import re
        t = token.strip()
        if re.search(r'\b(true|false)\b', t):
            return 'bool'
        if re.search(r'\b0x[a-fA-F0-9]{40}\b', t):
            return 'address'
        if re.search(r'\b(bytes|hex|abi\.encode|keccak256|sha256|ripemd160)\b', t):
            return 'bytes'
        if re.search(r'\b\d+\b', t):
            return 'uint256'
        if re.search(r'\baddress\b', t):
            return 'address'
        return 'uint256'

    def _synthesize_interface_from_context(self, interface_name: str, manifest: SymbolManifest) -> str:
        import re
        method_map = {}
        for orphan in manifest.orphans:
            for call in getattr(orphan, 'call_expressions', []):
                if interface_name not in call:
                    continue
                m = re.search(r'([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\s*\((.*)\)', call)
                if not m:
                    continue
                fn_name = m.group(2)
                raw_args = m.group(3).strip()
                args = [] if not raw_args else [a.strip() for a in raw_args.split(',')]
                arg_types = [self._infer_arg_type(a) for a in args if a]
                sig_key = (fn_name, tuple(arg_types))
                if sig_key not in method_map:
                    method_map[sig_key] = f"function {fn_name}({', '.join(arg_types)}) external returns (uint256);" if arg_types else f"function {fn_name}() external returns (uint256);"

        if not method_map:
            return f"interface {interface_name} {{}}"
        body = '\n    '.join(method_map.values())
        return f"interface {interface_name} {{\n    {body}\n}}"
    
    def _build_interfaces_prompt(self, interface_names: list, manifest: SymbolManifest) -> str:
        """Generate a structured repair plan for missing interfaces."""
        actions = []
        for interface_name in interface_names:
            body = self._synthesize_interface_from_context(interface_name, manifest)
            if body:
                actions.append(RepairAction(action='add_type_definition', target=interface_name, details={'code': body}))

        if not actions:
            return json.dumps({
                'category': 'undefined-type',
                'rationale': 'No direct evidence for interface synthesis.',
                'actions': [],
                'reject_reason': 'insufficient evidence',
            })

        plan = RepairPlan(
            category='undefined-type',
            rationale='Synthesize minimal interfaces from direct call/member evidence.',
            actions=actions,
        )
        return plan.model_dump_json()

    def _detect_proxy_url(self) -> str | None:
        proxy_url = os.getenv('HTTPX_PROXY_URL')
        if proxy_url:
            return proxy_url

        for name in ('HTTPS_PROXY', 'https_proxy', 'HTTP_PROXY', 'http_proxy'):
            value = os.getenv(name)
            if value:
                return value

        try:
            result = subprocess.run(
                ["bash", "-lc", "env | awk -F= '/^(HTTPS_PROXY|https_proxy|HTTP_PROXY|http_proxy)=/ {print $2; exit}'"],
                capture_output=True,
                text=True,
                check=False,
            )
            value = (result.stdout or "").strip()
            return value or None
        except Exception:
            return None

    def _raw_chat_completion(self, base_url: str, messages: list[dict], response_format: dict | None = None, trust_env: bool = True, proxy_url: str | None = None) -> str:
        url = base_url.rstrip('/') + '/chat/completions'
        payload = {
            'model': self.model,
            'messages': messages,
        }
        if response_format is not None:
            payload['response_format'] = response_format
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
        }
        client_kwargs = {'timeout': 180.0, 'trust_env': trust_env}
        if proxy_url:
            client_kwargs['proxy'] = proxy_url
        with httpx.Client(**client_kwargs) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data['choices'][0]['message']['content']

    def _call_opencode(self, system_prompt: str, prompt: str, json_mode: bool = False) -> str:
        combined_prompt = (
            f"{system_prompt}\n\n"
            f"User task:\n{prompt}\n\n"
        )
        if json_mode:
            combined_prompt += "Return only valid JSON. Do not wrap it in markdown.\n"
        else:
            combined_prompt += "Return only the requested content. Do not perform file operations.\n"

        prompt_path = None
        try:
            message = combined_prompt
            cmd = [self.opencode_bin, "run", "--model", self.model, "--format", "json"]
            if len(combined_prompt) > 100_000:
                temp_dir = None
                if self.opencode_dir:
                    temp_dir = Path(self.opencode_dir) / "runs" / "sol_resurrect" / "opencode_prompts"
                    temp_dir.mkdir(parents=True, exist_ok=True)
                with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", dir=temp_dir, delete=False) as prompt_file:
                    prompt_file.write(combined_prompt)
                    prompt_path = prompt_file.name
                cmd.extend(["Follow the attached prompt exactly.", "--file", prompt_path])
            else:
                cmd.append(message)
            if self.opencode_dir:
                cmd.extend(["--dir", self.opencode_dir])

            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                check=False,
            )
            if proc.returncode != 0:
                stderr = (proc.stderr or "").strip()
                stdout = (proc.stdout or "").strip()
                raise RuntimeError(f"opencode exited {proc.returncode}: {(stderr or stdout)[:1000]}")

            chunks = []
            for line in (proc.stdout or "").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("type") == "text":
                    text = event.get("part", {}).get("text")
                    if text:
                        chunks.append(text)
            content = "".join(chunks).strip()
            if not content:
                raise RuntimeError("opencode returned no text content")
            if json_mode:
                content = self._extract_json_object(content)
            return content
        finally:
            if prompt_path:
                try:
                    Path(prompt_path).unlink()
                except OSError:
                    pass

    def _extract_json_object(self, content: str) -> str:
        stripped = content.strip()
        if stripped.startswith("```json"):
            stripped = stripped[7:].strip()
        if stripped.startswith("```"):
            stripped = stripped[3:].strip()
        if stripped.endswith("```"):
            stripped = stripped[:-3].strip()

        decoder = json.JSONDecoder()
        for idx, char in enumerate(stripped):
            if char not in "[{":
                continue
            try:
                obj, _ = decoder.raw_decode(stripped[idx:])
                return json.dumps(obj, ensure_ascii=False)
            except json.JSONDecodeError:
                continue
        raise RuntimeError("opencode did not return a valid JSON object")

    def _call_llm(self, prompt: str) -> str:
        if self.provider == "opencode":
            return self._call_opencode("You are a JSON generator.", prompt, json_mode=True)

        last_exc = None
        messages = [{"role": "system", "content": "You are a JSON generator."}, {"role": "user", "content": prompt}]
        for base_url, client in self._clients:
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    response_format={"type": "json_object"}
                )
                self.client = client
                return response.choices[0].message.content
            except Exception as exc:
                last_exc = exc
                print(f"[WARN] LLM JSON call failed via {base_url}: {exc}")
                try:
                    content = self._raw_chat_completion(base_url, messages, response_format={"type": "json_object"}, trust_env=False, proxy_url=self._proxy_url)
                    print(f"[INFO] LLM JSON fallback succeeded via raw HTTP {base_url}")
                    return content
                except Exception as raw_exc:
                    last_exc = raw_exc
                    print(f"[WARN] LLM JSON raw HTTP fallback failed via {base_url}: {raw_exc}")
                    continue
        raise RuntimeError(f"All LLM JSON endpoints failed: {last_exc}")

    def _call_llm_text(self, prompt: str) -> str:
        if self.provider == "opencode":
            content = self._call_opencode(
                "You are a Solidity code generator. Output only valid, compilable Solidity code.",
                prompt,
            )
            return self._sanitize_llm_output(content)

        last_exc = None
        messages = [{"role": "system", "content": "You are a Solidity code generator. Output only valid, compilable Solidity code."}, {"role": "user", "content": prompt}]
        content = None
        for base_url, client in self._clients:
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages
                )
                self.client = client
                content = response.choices[0].message.content
                break
            except Exception as exc:
                last_exc = exc
                print(f"[WARN] LLM text call failed via {base_url}: {exc}")
                try:
                    content = self._raw_chat_completion(base_url, messages, trust_env=False, proxy_url=self._proxy_url)
                    print(f"[INFO] LLM text fallback succeeded via raw HTTP {base_url}")
                    break
                except Exception as raw_exc:
                    last_exc = raw_exc
                    print(f"[WARN] LLM text raw HTTP fallback failed via {base_url}: {raw_exc}")
                    continue
        else:
            raise RuntimeError(f"All LLM text endpoints failed: {last_exc}")

        content = self._sanitize_llm_output(content)
        return content

    def _is_valid_solidity_content(self, code: str) -> bool:
        """Check if the returned code looks like valid Solidity."""
        if not code or len(code.strip()) < 5:
            return False
        # Check the ORIGINAL (non-stripped) code for structural issues
        original_lines = code.split('\n')
        # Find first non-empty, non-comment line in original code
        first_content_line = None
        first_content_raw = ''
        for line in original_lines:
            s = line.strip()
            if not s or s.startswith('//') or s.startswith('*') or s.startswith('/*'):
                continue
            first_content_line = s
            first_content_raw = line
            break
        if first_content_line is None:
            return False
        # Check 1: First code line is an orphaned declaration (error/function without container)
        orphan_keywords = ('function ', 'error ', 'event ', 'modifier ', 'using ')
        if first_content_line.startswith(orphan_keywords):
            return False
        # Check 2: Code starts with stray closing brace
        if first_content_line.startswith('}') or first_content_line == '}':
            return False
        # Check 3: Code ends with a stray closing brace (more } than {)
        open_braces = code.count('{')
        close_braces = code.count('}')
        if close_braces > open_braces:
            return False
        # Stripped version checks
        stripped = code.strip()
        valid_starts = [
            'contract', 'library', 'interface', 'abstract', 'struct', 'enum',
            'type', 'error', 'function', 'modifier', 'event', 'using', 'import',
            'pragma', '//', '/*',
        ]
        first_word = stripped.split()[0] if stripped.split() else ''
        if first_word not in valid_starts and first_word != '//' and not first_word.startswith('/*'):
            return False
        # Must contain at least one Solidity structural element
        has_structure = any(kw in stripped for kw in ['{', ';', 'function'])
        if not has_structure:
            return False
        # Must NOT contain plain English paragraphs
        lines = stripped.split('\n')
        non_code_count = 0
        for line in lines:
            s = line.strip()
            if not s or s.startswith('//') or s.startswith('/*') or s.startswith('*'):
                continue
            words = s.split()
            if len(words) >= 5 and '{' not in s and '}' not in s and ';' not in s and '//' not in s:
                if not any(kw in s for kw in ['function', 'contract', 'interface', 'library', 'struct', 'enum', 'error', 'type', 'import', 'pragma', 'using', 'modifier', 'event']):
                    non_code_count += 1
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith('//') and not l.strip().startswith('/*') and not l.strip().startswith('*')]
        if code_lines and non_code_count / len(code_lines) > 0.3:
            return False
        return True

    def _sanitize_llm_output(self, content: str) -> str:
        """Sanitize LLM output: remove junk, extract only valid Solidity code blocks."""
        import re

        if not content:
            return ""

        # Step 1: Extract fenced code blocks if present
        code_blocks = re.findall(r'```(?:solidity|sol)?\s*\n(.*?)```', content, re.DOTALL)
        if code_blocks:
            # Use the longest block (usually the main one)
            content = max(code_blocks, key=len).strip()
        else:
            # Remove common markdown fences that might be incomplete
            content = re.sub(r'^```(?:solidity|sol)?\s*\n?', '', content)
            content = re.sub(r'\n?```\s*$', '', content)

        # Step 1.5: Remove headers and imports that won't work in a self-contained file
        content = re.sub(r'^// SPDX-License-Identifier:\s*\S+.*\n?', '', content, flags=re.MULTILINE)
        content = re.sub(r'^pragma solidity\s+[^;]+;\n?', '', content, flags=re.MULTILINE)
        content = re.sub(r"^import\s+[^;]+;\n?", '', content, flags=re.MULTILINE)

        # Step 2: Remove lines that are clearly not Solidity code
        non_code_patterns = [
            r'^Here\s+is\b', r'^Here\'s\b', r'^The\s+(?:following|code|generated|complete|generated)\b',
            r'^Note:?\b', r'^Please\b', r'^Make sure\b', r'^This\s+(?:is|code|contract|file)\b',
            r'^I\'ll\b', r'^I will\b', r'^Let me\b', r'^You can\b',
            r'^\*\*', r'^#{1,4}\s', r'^OK\b', r'^Sure\b',
            r'^Below\b', r'^Above\b',
            # Catch common LLM English output
            r'^No\s+\w+\s+(?:elements|interface|functions|methods|content|information)',
            r'^The\s+`\w+`\s+parameter',
            r'^No\s+specific\s+\w+\s+functions',
            r'^It\s+(?:is|appears|looks|seems)\b',
            r'^This\s+(?:means|would|should|could|will|can)\b',
            r'^As\s+(?:a\s+)?result',
            r'^In\s+this\s+case',
            r'^For\s+(?:this|the|example|instance)',
            r'^We\s+(?:can|need|will|should|have)\b',
            r'^If\s+(?:you|we|the)\b',
            r'^To\s+(?:make|ensure|fix|handle|avoid|do|use)\b',
        ]
        lines = content.split('\n')
        filtered = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                filtered.append(line)
                continue
            if any(re.match(p, stripped, re.I) for p in non_code_patterns):
                continue
            # Skip lines that look like markdown bullet points without code
            if re.match(r'^[-*]\s+\w', stripped) and '//' not in stripped and '{' not in stripped and ';' not in stripped:
                continue
            filtered.append(line)
        content = '\n'.join(filtered).strip()

        # Step 3: Remove trailing non-code paragraphs
        # Find the last Solidity-like line (ends with ; or } or starts with known keyword)
        solidity_end_patterns = [
            r'^\s*(?:contract|library|interface|abstract|struct|enum|type|error|function|modifier|event|using|import|pragma|//|/\*)',
            r'[;{}]\s*$',
        ]
        lines = content.split('\n')
        last_code_line = -1
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue
            if any(re.match(p, stripped) for p in solidity_end_patterns):
                last_code_line = i
        if last_code_line >= 0 and last_code_line < len(lines) - 1:
            # Check if remaining lines are non-code
            remaining = '\n'.join(lines[last_code_line + 1:])
            if not any(kw in remaining for kw in ['contract', 'function', 'struct', 'interface', 'library', '{', '}']):
                content = '\n'.join(lines[:last_code_line + 1])

        # Step 4: Balance braces and parens
        open_braces = content.count('{')
        close_braces = content.count('}')
        if open_braces > close_braces:
            content += '\n' + ('}\n' * (open_braces - close_braces))
        open_parens = content.count('(')
        close_parens = content.count(')')
        if open_parens > close_parens:
            content += ')' * (open_parens - close_parens)

        return content.strip()
    
    def _detect_missing_mocks(self, manifest: SymbolManifest) -> list:
        """检测代码中使用但未定义的 Mock 合约类型"""
        import re
        from .symbol_table import build_symbol_table

        all_code = []
        for contract in manifest.contracts.values():
            all_code.append(contract.code)
        combined_code = '\n'.join(all_code)
        symbol_table = build_symbol_table(combined_code + '\n' + '\n'.join(manifest.global_types))

        used_types = set()
        for orphan in manifest.orphans:
            for call in getattr(orphan, 'call_expressions', []):
                m = re.search(r'new\s+(I[A-Z][A-Za-z0-9_]*|[A-Z][A-Za-z0-9_]*)', call)
                if m:
                    used_types.add(m.group(1))
            for member_access in getattr(orphan, 'member_accesses', []):
                m = re.match(r'(I[A-Z][A-Za-z0-9_]*|[A-Z][A-Za-z0-9_]*)\.', member_access)
                if m:
                    used_types.add(m.group(1))

        defined_types = symbol_table.all_names()
        builtins = {'Actual', 'Alice', 'Auto', 'Available', 'Baseline', 'Bob', 'Charlie', 'Context', 'Dave', 'Error'}
        return sorted(t for t in used_types - defined_types if t not in builtins)
    
    def _find_nested_types(self, mock_name: str, manifest: SymbolManifest) -> list[str]:
        """查找形如 MockName.Struct 的嵌套类型引用"""
        import re
        pattern = re.compile(rf'\b{re.escape(mock_name)}\.([A-Z]\w+)')
        nested = set()
        # 搜索全局类型和合约代码
        for g_type in manifest.global_types:
            nested.update(pattern.findall(g_type))
        for contract in manifest.contracts.values():
            nested.update(pattern.findall(contract.code))
        return sorted(nested)
    
    def _build_mock_contracts_prompt(self, mock_names: list, manifest: SymbolManifest) -> str:
        """生成缺失 Mock 合约的 prompt —— 收集完整调用上下文"""
        import re
        contexts = []

        # 收集所有代码用于分析
        all_code_blocks = []
        for g_type in manifest.global_types:
            all_code_blocks.append(g_type)
        for contract in manifest.contracts.values():
            all_code_blocks.append(contract.code)
        for orphan in manifest.orphans:
            all_code_blocks.append(orphan.code)
        all_text = '\n'.join(all_code_blocks)

        for mock_name in mock_names:
            # 1. 查找嵌套类型引用
            nested_types = self._find_nested_types(mock_name, manifest)

            # 2. 收集使用此 mock 的所有代码片段
            usage_snippets = []
            for block in all_code_blocks:
                if mock_name in block:
                    usage_snippets.append(block)

            # 3. 提取在 mock 上调用的所有方法
            method_calls = []
            # Pattern: mockName.method(...)
            method_pattern = rf'\b{re.escape(mock_name)}\.(\w+)\s*\('
            for match in re.finditer(method_pattern, all_text):
                method_calls.append(match.group(0))
            # Pattern: typed_var.method(...) where var is typed as mockName
            type_usage_pattern = rf'{re.escape(mock_name)}\s+(?:memory|storage|calldata)?\s*(\w+)'
            for match in re.finditer(type_usage_pattern, all_text):
                var_name = match.group(1)
                var_method_pattern = rf'\b{re.escape(var_name)}\.(\w+)\s*\([^)]*\)'
                for mm in re.finditer(var_method_pattern, all_text):
                    method_calls.append(mm.group(0))

            # 4. 提取 abi.decode 中使用的所有结构体类型
            used_structs = set()
            for code in usage_snippets:
                decode_pattern = r'abi\.decode\([^,]+,\s*\(([^)]+)\)\)'
                for decode_match in re.finditer(decode_pattern, code):
                    types_str = decode_match.group(1)
                    type_names = re.findall(r'\b([A-Z]\w+)(?:\[\])?\b', types_str)
                    used_structs.update(type_names)

            # 5. 提取 new 此类实例的模式
            new_patterns = rf'new\s+{re.escape(mock_name)}\s*\('
            new_usages = re.findall(new_patterns, all_text)

            # 6. 提取成员访问模式
            member_accesses = re.findall(rf'\b{re.escape(mock_name)}\.(\w+)', all_text)

            # 构建上下文
            context_parts = []
            context_parts.append(f"Mock name: {mock_name}")
            if usage_snippets:
                # Show first 3 snippets, truncated
                for i, snippet in enumerate(usage_snippets[:3]):
                    truncated = snippet[:1500] if len(snippet) > 1500 else snippet
                    context_parts.append(f"Usage snippet {i+1}:\n{truncated}")
            if method_calls:
                unique_calls = list(dict.fromkeys(method_calls))[:20]
                context_parts.append(f"Observed method calls:\n" + "\n".join(f"  {c}" for c in unique_calls))
            if nested_types:
                context_parts.append(f"Nested types needed: {', '.join(f'{mock_name}.{t}' for t in nested_types)}")
            if used_structs:
                context_parts.append(f"Abi.decode structs used: {', '.join(sorted(used_structs))}")
            if member_accesses:
                context_parts.append(f"Member accesses: {', '.join(sorted(set(member_accesses))[:20])}")

            contexts.append('\n'.join(context_parts))

        combined_contexts = '\n\n' + ('=' * 40) + '\n\n'.join(contexts)
        names_str = ", ".join(mock_names)

        return f"""
Generate minimal, compilable Solidity Mock contracts for: {names_str}.

DETAILED CONTEXTS:{combined_contexts}

{self._solidity_rules}

CRITICAL REQUIREMENTS:
1. Create a standalone, compilable contract for EACH requested mock name.
2. Implement EVERY method observed in the method calls section with the CORRECT signatures.
3. Return PASS-THROUGH values: if a function returns uint256, return a plausible non-zero value (use input parameters or a stored mock value). Do NOT return 0 unless the context clearly demands it.
4. Define ALL nested struct types (e.g., MockName.PoolInfo) DIRECTLY INSIDE the contract body — do NOT reference external definitions.
5. Define ALL error types that the contract might revert with.
6. For structs used in abi.decode, create complete struct definitions with ALL fields that could be decoded.
7. Include state variables to store mock data that setter functions can configure.
8. Provide `setMock*` functions for any stored state so tests can configure the mock.
9. Output ONLY valid Solidity code — ALL requested contracts together, no file header, no SPDX, no pragma.
10. Do NOT import or reference any external contracts, interfaces, or libraries.
11. Keep the implementation self-contained and generic.
12. If a method requires returning a complex type (struct), create the struct and return an initialized instance.
"""

    
    def _detect_missing_errors(self, manifest: SymbolManifest) -> list:
        """检测代码中使用但未定义的自定义错误"""
        import re
        
        # 收集所有代码片段
        all_code = []
        for orphan in manifest.orphans:
            all_code.append(orphan.code)
        for contract in manifest.contracts.values():
            all_code.append(contract.code)
        
        combined_code = '\n'.join(all_code)
        
        # 查找 revert ErrorName(...) 模式
        revert_pattern = r'revert\s+([A-Z]\w+)\s*\('
        used_errors = set(re.findall(revert_pattern, combined_code))
        
        # 收集已定义的错误
        defined_errors = set(re.findall(r'\berror\s+(\w+)', combined_code))
        
        # 缺失的错误 = 使用的 - 已定义的
        missing = used_errors - defined_errors
        
        return list(missing)
    
    def _generate_error_definitions(self, error_names: list) -> str:
        """为缺失的错误生成定义"""
        lines = ["// Auto-generated error definitions"]
        for error_name in sorted(error_names):
            lines.append(f"error {error_name}();")
        return '\n'.join(lines)
