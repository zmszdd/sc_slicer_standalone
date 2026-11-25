; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd6198c56_caller_controlled_against_msg_sender () Bool)
(declare-fun cd6198c56_redeem_or_withdraw_called_with_owner () Bool)
(declare-fun cd6198c56_user_funds_lost () Bool)
(declare-fun cd6198c56_user_permit_approval_created () Bool)
(declare-fun cd6198c56_user_redeem_request_submitted () Bool)
(assert
 (= cd6198c56_caller_controlled_against_msg_sender cd6198c56_caller_controlled_against_msg_sender))
(assert
 (= cd6198c56_redeem_or_withdraw_called_with_owner cd6198c56_redeem_or_withdraw_called_with_owner))
(assert
 (= cd6198c56_user_funds_lost cd6198c56_user_funds_lost))
(assert
 (= cd6198c56_user_permit_approval_created cd6198c56_user_permit_approval_created))
(assert
 (= cd6198c56_user_redeem_request_submitted cd6198c56_user_redeem_request_submitted))
(define-fun report_preconditions () Bool (and cd6198c56_user_permit_approval_created
     cd6198c56_user_redeem_request_submitted))
(define-fun report_safety () Bool (=> cd6198c56_redeem_or_withdraw_called_with_owner
    cd6198c56_caller_controlled_against_msg_sender))
(define-fun report_effects () Bool (and cd6198c56_redeem_or_withdraw_called_with_owner
     (not cd6198c56_caller_controlled_against_msg_sender)
     cd6198c56_user_funds_lost))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
