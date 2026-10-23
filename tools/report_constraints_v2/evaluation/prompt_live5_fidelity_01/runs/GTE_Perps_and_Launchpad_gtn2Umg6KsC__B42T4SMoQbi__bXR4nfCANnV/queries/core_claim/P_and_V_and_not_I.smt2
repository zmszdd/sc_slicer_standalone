; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
 (declare-fun stake_operation_occurred () Bool)
(declare-fun reward_recipient () ReportAddress)
(declare-fun staking_user () ReportAddress)
(assert
 (= stake_operation_occurred stake_operation_occurred))
(assert
 (= reward_recipient reward_recipient))
(assert
 (= staking_user staking_user))
(define-fun report_preconditions () Bool stake_operation_occurred)
(define-fun report_safety () Bool (=> stake_operation_occurred (= reward_recipient staking_user)))
(define-fun report_effects () Bool (and stake_operation_occurred (not (= reward_recipient staking_user))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
