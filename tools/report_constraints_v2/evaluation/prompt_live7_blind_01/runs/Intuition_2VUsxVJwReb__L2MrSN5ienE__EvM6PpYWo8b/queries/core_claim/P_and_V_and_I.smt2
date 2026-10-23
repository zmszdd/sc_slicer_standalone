; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun owner_is_contract () Bool)
(declare-fun owner_has_private_key () Bool)
(declare-fun recovered_equals_owner () Bool)
(assert
 (= owner_is_contract owner_is_contract))
(assert
 (= owner_has_private_key owner_has_private_key))
(assert
 (= recovered_equals_owner recovered_equals_owner))
(define-fun report_preconditions () Bool (and owner_is_contract (not owner_has_private_key)))
(define-fun report_safety () Bool (=> (and owner_is_contract (not owner_has_private_key)) recovered_equals_owner))
(define-fun report_effects () Bool (and owner_is_contract (not owner_has_private_key) (not recovered_equals_owner)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
