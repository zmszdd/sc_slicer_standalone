; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cc2ee2d34_caller_has_validator_role () Bool)
(declare-fun cc2ee2d34_destination_is_kyc_verified () Bool)
(declare-fun cc2ee2d34_kyc_gate_enforced_on_batch_path () Bool)
(declare-fun cc2ee2d34_onchain_kyc_guarantee_reliable () Bool)
(declare-fun cc2ee2d34_source_is_kyc_verified () Bool)
(assert
 (= cc2ee2d34_caller_has_validator_role cc2ee2d34_caller_has_validator_role))
(assert
 (= cc2ee2d34_destination_is_kyc_verified cc2ee2d34_destination_is_kyc_verified))
(assert
 (= cc2ee2d34_kyc_gate_enforced_on_batch_path cc2ee2d34_kyc_gate_enforced_on_batch_path))
(assert
 (= cc2ee2d34_onchain_kyc_guarantee_reliable cc2ee2d34_onchain_kyc_guarantee_reliable))
(assert
 (= cc2ee2d34_source_is_kyc_verified cc2ee2d34_source_is_kyc_verified))
(define-fun report_preconditions () Bool (and cc2ee2d34_caller_has_validator_role
     cc2ee2d34_source_is_kyc_verified
     (not cc2ee2d34_destination_is_kyc_verified)))
(define-fun report_safety () Bool (=> (and cc2ee2d34_caller_has_validator_role
         cc2ee2d34_source_is_kyc_verified
         (not cc2ee2d34_destination_is_kyc_verified))
    (and cc2ee2d34_kyc_gate_enforced_on_batch_path
         cc2ee2d34_onchain_kyc_guarantee_reliable)))
(define-fun report_effects () Bool (and cc2ee2d34_caller_has_validator_role
     cc2ee2d34_source_is_kyc_verified
     (not cc2ee2d34_destination_is_kyc_verified)
     (not (and cc2ee2d34_kyc_gate_enforced_on_batch_path
               cc2ee2d34_onchain_kyc_guarantee_reliable))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
