; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cfdfe7073_actual_below_limit () Bool)
(declare-fun cfdfe7073_new_stake_attempted_flag () Bool)
(declare-fun cfdfe7073_new_stake_prevented () Bool)
(declare-fun cfdfe7073_slashed_funds_exist_flag () Bool)
(assert
 (= cfdfe7073_actual_below_limit cfdfe7073_actual_below_limit))
(assert
 (= cfdfe7073_new_stake_attempted_flag cfdfe7073_new_stake_attempted_flag))
(assert
 (= cfdfe7073_new_stake_prevented cfdfe7073_new_stake_prevented))
(assert
 (= cfdfe7073_slashed_funds_exist_flag cfdfe7073_slashed_funds_exist_flag))
(define-fun report_preconditions () Bool (and cfdfe7073_slashed_funds_exist_flag cfdfe7073_new_stake_attempted_flag))
(define-fun report_safety () Bool (=> (and cfdfe7073_new_stake_attempted_flag cfdfe7073_actual_below_limit)
    (not cfdfe7073_new_stake_prevented)))
(define-fun report_effects () Bool (and cfdfe7073_new_stake_attempted_flag
     cfdfe7073_actual_below_limit
     cfdfe7073_new_stake_prevented
     (and cfdfe7073_new_stake_prevented cfdfe7073_actual_below_limit)
     (and cfdfe7073_new_stake_prevented cfdfe7073_actual_below_limit)))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
