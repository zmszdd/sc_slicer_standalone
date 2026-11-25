; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c1292998a_slashed_funds_present () Bool)
(declare-fun c1292998a_slashed_treatment_in_exchange_ratio () Bool)
(declare-fun c1292998a_slashed_treatment_in_limit_check () Bool)
(assert
 (= c1292998a_slashed_funds_present c1292998a_slashed_funds_present))
(assert
 (= c1292998a_slashed_treatment_in_exchange_ratio c1292998a_slashed_treatment_in_exchange_ratio))
(assert
 (= c1292998a_slashed_treatment_in_limit_check c1292998a_slashed_treatment_in_limit_check))
(define-fun report_preconditions () Bool c1292998a_slashed_funds_present)
(define-fun report_safety () Bool (=> c1292998a_slashed_funds_present
    (= c1292998a_slashed_treatment_in_limit_check
       c1292998a_slashed_treatment_in_exchange_ratio)))
(define-fun report_effects () Bool (and c1292998a_slashed_funds_present
     (not (= c1292998a_slashed_treatment_in_limit_check
             c1292998a_slashed_treatment_in_exchange_ratio))
     c1292998a_slashed_treatment_in_exchange_ratio
     (not c1292998a_slashed_treatment_in_limit_check)
     c1292998a_slashed_funds_present))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
