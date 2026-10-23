; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7b031dad_batch_movement_executed () Bool)
(declare-fun c7b031dad_kyc_gate_enforced () Bool)
(declare-fun c7b031dad_token_paused () Bool)
(declare-fun c7b031dad_validator_authorized () Bool)
(assert
 (= c7b031dad_batch_movement_executed c7b031dad_batch_movement_executed))
(assert
 (= c7b031dad_kyc_gate_enforced c7b031dad_kyc_gate_enforced))
(assert
 (= c7b031dad_token_paused c7b031dad_token_paused))
(assert
 (= c7b031dad_validator_authorized c7b031dad_validator_authorized))
(define-fun report_preconditions () Bool (and c7b031dad_validator_authorized c7b031dad_kyc_gate_enforced))
(define-fun report_safety () Bool (=> (and c7b031dad_token_paused c7b031dad_validator_authorized)
    (not c7b031dad_batch_movement_executed)))
(define-fun report_effects () Bool (and c7b031dad_token_paused
     c7b031dad_validator_authorized
     (not (not c7b031dad_batch_movement_executed))))
