; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun batch_uses_multicall () Bool)
(declare-fun is_multicall_flag () Bool)
(declare-fun inner_multicall_frontloaded () Bool)
(declare-fun uses_delegatecall_self () Bool)
(declare-fun no_delegatecall_guard_pass () Bool)
(declare-fun payment_check_reverts () Bool)
(assert
 (= batch_uses_multicall batch_uses_multicall))
(assert
 (= is_multicall_flag is_multicall_flag))
(assert
 (= inner_multicall_frontloaded inner_multicall_frontloaded))
(assert
 (= uses_delegatecall_self uses_delegatecall_self))
(assert
 (= no_delegatecall_guard_pass no_delegatecall_guard_pass))
(assert
 (= payment_check_reverts payment_check_reverts))
(define-fun report_preconditions () Bool (and batch_uses_multicall
     is_multicall_flag
     inner_multicall_frontloaded
     uses_delegatecall_self
     no_delegatecall_guard_pass))
(define-fun report_safety () Bool (=> (and batch_uses_multicall
         is_multicall_flag
         inner_multicall_frontloaded
         uses_delegatecall_self)
    (not payment_check_reverts)))
(define-fun report_effects () Bool (and batch_uses_multicall
     is_multicall_flag
     inner_multicall_frontloaded
     uses_delegatecall_self
     payment_check_reverts))
(assert report_preconditions)
(check-sat)
(get-model)
