; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c75fa9275_hash_excludes_signature () Bool)
(declare-fun c75fa9275_signature_suffix_bytes () Int)
(declare-fun c75fa9275_signature_total_bytes () Int)
(declare-fun c75fa9275_signed_window_authenticated () Bool)
(declare-fun c75fa9275_window_rewritten () Bool)
(assert
 (= c75fa9275_hash_excludes_signature c75fa9275_hash_excludes_signature))
(assert
 (= c75fa9275_signature_suffix_bytes c75fa9275_signature_suffix_bytes))
(assert
 (= c75fa9275_signature_total_bytes c75fa9275_signature_total_bytes))
(assert
 (= c75fa9275_signed_window_authenticated c75fa9275_signed_window_authenticated))
(assert
 (= c75fa9275_window_rewritten c75fa9275_window_rewritten))
(define-fun report_preconditions () Bool (and (= 77 c75fa9275_signature_total_bytes)
     (= 12 c75fa9275_signature_suffix_bytes)
     c75fa9275_hash_excludes_signature))
(define-fun report_safety () Bool (=> (and c75fa9275_hash_excludes_signature
         (= 12 c75fa9275_signature_suffix_bytes)
         c75fa9275_window_rewritten)
    (and c75fa9275_signed_window_authenticated (not c75fa9275_window_rewritten))))
(define-fun report_effects () Bool (and c75fa9275_hash_excludes_signature
     (= 12 c75fa9275_signature_suffix_bytes)
     c75fa9275_window_rewritten
     (not (and c75fa9275_signed_window_authenticated
               (not c75fa9275_window_rewritten)))))
