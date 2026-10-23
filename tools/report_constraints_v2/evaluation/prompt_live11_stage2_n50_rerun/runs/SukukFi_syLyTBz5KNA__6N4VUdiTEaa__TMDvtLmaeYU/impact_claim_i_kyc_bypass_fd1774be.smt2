; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9d681199_caller_is_validator () Bool)
(declare-fun c9d681199_destination_is_kyc_verified () Bool)
(declare-fun c9d681199_funds_routed_to_non_kyc () Bool)
(declare-fun c9d681199_kyc_gate_enforced () Bool)
(declare-fun c9d681199_source_is_kyc_verified () Bool)
(assert
 (= c9d681199_caller_is_validator c9d681199_caller_is_validator))
(assert
 (= c9d681199_destination_is_kyc_verified c9d681199_destination_is_kyc_verified))
(assert
 (= c9d681199_funds_routed_to_non_kyc c9d681199_funds_routed_to_non_kyc))
(assert
 (= c9d681199_kyc_gate_enforced c9d681199_kyc_gate_enforced))
(assert
 (= c9d681199_source_is_kyc_verified c9d681199_source_is_kyc_verified))
(define-fun report_preconditions () Bool (and c9d681199_caller_is_validator
     c9d681199_source_is_kyc_verified
     (not c9d681199_destination_is_kyc_verified)))
(define-fun report_safety () Bool (=> (and c9d681199_caller_is_validator
         c9d681199_source_is_kyc_verified
         (not c9d681199_destination_is_kyc_verified))
    (or c9d681199_kyc_gate_enforced (not c9d681199_funds_routed_to_non_kyc))))
(define-fun report_effects () Bool (and c9d681199_caller_is_validator
     c9d681199_source_is_kyc_verified
     (not c9d681199_destination_is_kyc_verified)
     (not (or c9d681199_kyc_gate_enforced
              (not c9d681199_funds_routed_to_non_kyc)))))
