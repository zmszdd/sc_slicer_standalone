; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c17edcf5c_attacker_intercepted_signature () Bool)
(declare-fun c17edcf5c_executed_outside_time_bounds () Bool)
(declare-fun c17edcf5c_signature_length_bytes () Int)
(declare-fun c17edcf5c_suffix_present () Bool)
(assert
 (= c17edcf5c_attacker_intercepted_signature c17edcf5c_attacker_intercepted_signature))
(assert
 (= c17edcf5c_executed_outside_time_bounds c17edcf5c_executed_outside_time_bounds))
(assert
 (= c17edcf5c_signature_length_bytes c17edcf5c_signature_length_bytes))
(assert
 (= c17edcf5c_suffix_present c17edcf5c_suffix_present))
(define-fun report_preconditions () Bool (and (= 77 c17edcf5c_signature_length_bytes)
     c17edcf5c_suffix_present
     c17edcf5c_attacker_intercepted_signature))
(define-fun report_safety () Bool (=> (and c17edcf5c_suffix_present (= 77 c17edcf5c_signature_length_bytes))
    (not c17edcf5c_executed_outside_time_bounds)))
(define-fun report_effects () Bool (and c17edcf5c_suffix_present
     (= 77 c17edcf5c_signature_length_bytes)
     (not (not c17edcf5c_executed_outside_time_bounds))))
