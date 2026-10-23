; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c3f41bc85_attacker_kyc_verified () Bool)
(declare-fun c3f41bc85_receiver_kyc_verified () Bool)
(declare-fun c3f41bc85_underlying_assets_received () Bool)
(declare-fun c3f41bc85_victim_self_allowance_sufficient () Bool)
(assert
 (= c3f41bc85_attacker_kyc_verified c3f41bc85_attacker_kyc_verified))
(assert
 (= c3f41bc85_receiver_kyc_verified c3f41bc85_receiver_kyc_verified))
(assert
 (= c3f41bc85_underlying_assets_received c3f41bc85_underlying_assets_received))
(assert
 (= c3f41bc85_victim_self_allowance_sufficient c3f41bc85_victim_self_allowance_sufficient))
(define-fun report_preconditions () Bool (and c3f41bc85_victim_self_allowance_sufficient
     (not c3f41bc85_attacker_kyc_verified)))
(define-fun report_safety () Bool (=> c3f41bc85_underlying_assets_received
    (=> c3f41bc85_underlying_assets_received c3f41bc85_receiver_kyc_verified)))
(define-fun report_effects () Bool (and c3f41bc85_underlying_assets_received
     c3f41bc85_underlying_assets_received
     (not c3f41bc85_receiver_kyc_verified)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
