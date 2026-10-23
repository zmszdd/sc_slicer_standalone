; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cae632da9_caller_is_validator () Bool)
(declare-fun cae632da9_funds_routed_to_unverified () Bool)
(declare-fun cae632da9_recipient_is_kyc_verified () Bool)
(declare-fun cae632da9_standard_flows_kyc_gated () Bool)
(declare-fun cae632da9_validator_compromised () Bool)
(assert
 (= cae632da9_caller_is_validator cae632da9_caller_is_validator))
(assert
 (= cae632da9_funds_routed_to_unverified cae632da9_funds_routed_to_unverified))
(assert
 (= cae632da9_recipient_is_kyc_verified cae632da9_recipient_is_kyc_verified))
(assert
 (= cae632da9_standard_flows_kyc_gated cae632da9_standard_flows_kyc_gated))
(assert
 (= cae632da9_validator_compromised cae632da9_validator_compromised))
(define-fun report_preconditions () Bool (and cae632da9_caller_is_validator
     cae632da9_standard_flows_kyc_gated
     cae632da9_validator_compromised))
(define-fun report_safety () Bool (=> (and cae632da9_caller_is_validator
         cae632da9_validator_compromised
         (not cae632da9_recipient_is_kyc_verified))
    (not cae632da9_funds_routed_to_unverified)))
(define-fun report_effects () Bool (and cae632da9_caller_is_validator
     cae632da9_validator_compromised
     (not cae632da9_recipient_is_kyc_verified)
     (not (not cae632da9_funds_routed_to_unverified))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
