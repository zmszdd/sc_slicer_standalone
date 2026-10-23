; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cff7bba12_batch_settlement_kyc_gated () Bool)
(declare-fun cff7bba12_batch_settlement_restricted_to_validator () Bool)
(declare-fun cff7bba12_integrator_kyc_guarantee_reliable () Bool)
(declare-fun cff7bba12_source_funds_kyc_verified () Bool)
(declare-fun cff7bba12_standard_flows_kyc_gated () Bool)
(assert
 (= cff7bba12_batch_settlement_kyc_gated cff7bba12_batch_settlement_kyc_gated))
(assert
 (= cff7bba12_batch_settlement_restricted_to_validator cff7bba12_batch_settlement_restricted_to_validator))
(assert
 (= cff7bba12_integrator_kyc_guarantee_reliable cff7bba12_integrator_kyc_guarantee_reliable))
(assert
 (= cff7bba12_source_funds_kyc_verified cff7bba12_source_funds_kyc_verified))
(assert
 (= cff7bba12_standard_flows_kyc_gated cff7bba12_standard_flows_kyc_gated))
(define-fun report_preconditions () Bool (and cff7bba12_batch_settlement_restricted_to_validator
     cff7bba12_standard_flows_kyc_gated
     cff7bba12_source_funds_kyc_verified))
(define-fun report_safety () Bool (=> (and cff7bba12_batch_settlement_restricted_to_validator
         cff7bba12_standard_flows_kyc_gated
         cff7bba12_source_funds_kyc_verified)
    (and cff7bba12_batch_settlement_kyc_gated
         cff7bba12_integrator_kyc_guarantee_reliable)))
(define-fun report_effects () Bool (and cff7bba12_batch_settlement_restricted_to_validator
     cff7bba12_standard_flows_kyc_gated
     cff7bba12_source_funds_kyc_verified
     (not (and cff7bba12_batch_settlement_kyc_gated
               cff7bba12_integrator_kyc_guarantee_reliable))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
