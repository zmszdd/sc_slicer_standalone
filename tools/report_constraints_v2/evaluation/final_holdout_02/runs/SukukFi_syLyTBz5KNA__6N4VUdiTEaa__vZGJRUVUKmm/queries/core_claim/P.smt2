; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun recipient_kyc_verified () Bool)
(declare-fun standard_ops_kyc_enforced () Bool)
(declare-fun batch_functions_exposed () Bool)
(declare-fun caller_is_validator () Bool)
(declare-fun tokens_transferred_to_non_kyc () Bool)
(assert
 (= recipient_kyc_verified recipient_kyc_verified))
(assert
 (= standard_ops_kyc_enforced standard_ops_kyc_enforced))
(assert
 (= batch_functions_exposed batch_functions_exposed))
(assert
 (= caller_is_validator caller_is_validator))
(assert
 (= tokens_transferred_to_non_kyc tokens_transferred_to_non_kyc))
(define-fun report_preconditions () Bool (and standard_ops_kyc_enforced
     batch_functions_exposed
     caller_is_validator
     (not recipient_kyc_verified)))
(define-fun report_safety () Bool (=> (and batch_functions_exposed
         caller_is_validator
         (not recipient_kyc_verified))
    (not tokens_transferred_to_non_kyc)))
(define-fun report_effects () Bool (and batch_functions_exposed
     caller_is_validator
     (not recipient_kyc_verified)
     (not (not tokens_transferred_to_non_kyc))))
(assert report_preconditions)
(check-sat)
(get-model)
