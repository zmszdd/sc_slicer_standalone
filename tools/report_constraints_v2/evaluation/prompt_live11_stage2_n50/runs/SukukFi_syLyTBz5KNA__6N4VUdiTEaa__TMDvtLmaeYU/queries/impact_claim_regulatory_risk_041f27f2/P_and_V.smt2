; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbd444336_batch_moves_funds () Bool)
(declare-fun cbd444336_caller_is_validator () Bool)
(declare-fun cbd444336_kyc_gate_enforced () Bool)
(declare-fun cbd444336_recipient_kyc_verified () Bool)
(declare-fun cbd444336_validator_exercises_batch () Bool)
(assert
 (= cbd444336_batch_moves_funds cbd444336_batch_moves_funds))
(assert
 (= cbd444336_caller_is_validator cbd444336_caller_is_validator))
(assert
 (= cbd444336_kyc_gate_enforced cbd444336_kyc_gate_enforced))
(assert
 (= cbd444336_recipient_kyc_verified cbd444336_recipient_kyc_verified))
(assert
 (= cbd444336_validator_exercises_batch cbd444336_validator_exercises_batch))
(define-fun report_preconditions () Bool (and cbd444336_caller_is_validator
     cbd444336_recipient_kyc_verified
     cbd444336_validator_exercises_batch))
(define-fun report_safety () Bool (=> (and cbd444336_caller_is_validator
         cbd444336_validator_exercises_batch
         cbd444336_batch_moves_funds)
    cbd444336_kyc_gate_enforced))
(define-fun report_effects () Bool (and cbd444336_caller_is_validator
     cbd444336_validator_exercises_batch
     cbd444336_batch_moves_funds
     (not cbd444336_kyc_gate_enforced)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
