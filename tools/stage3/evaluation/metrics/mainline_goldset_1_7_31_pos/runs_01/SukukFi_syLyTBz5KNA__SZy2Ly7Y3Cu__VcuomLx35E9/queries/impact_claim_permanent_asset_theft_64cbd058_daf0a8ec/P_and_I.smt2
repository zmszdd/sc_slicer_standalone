; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce5046626_attacker_steals_user_underlying_assets () Bool)
(declare-fun ce5046626_caller_controlled_against_msg_sender () Bool)
(declare-fun ce5046626_redeem_or_withdraw_called_with_owner () Bool)
(declare-fun ce5046626_user_permit_approval_created () Bool)
(declare-fun ce5046626_user_redeem_request_submitted () Bool)
(assert
 (= ce5046626_attacker_steals_user_underlying_assets ce5046626_attacker_steals_user_underlying_assets))
(assert
 (= ce5046626_caller_controlled_against_msg_sender ce5046626_caller_controlled_against_msg_sender))
(assert
 (= ce5046626_redeem_or_withdraw_called_with_owner ce5046626_redeem_or_withdraw_called_with_owner))
(assert
 (= ce5046626_user_permit_approval_created ce5046626_user_permit_approval_created))
(assert
 (= ce5046626_user_redeem_request_submitted ce5046626_user_redeem_request_submitted))
(define-fun report_preconditions () Bool (and ce5046626_user_permit_approval_created
     ce5046626_user_redeem_request_submitted))
(define-fun report_safety () Bool (=> ce5046626_redeem_or_withdraw_called_with_owner
    ce5046626_caller_controlled_against_msg_sender))
(define-fun report_effects () Bool (and ce5046626_redeem_or_withdraw_called_with_owner
     (not ce5046626_caller_controlled_against_msg_sender)
     ce5046626_attacker_steals_user_underlying_assets
     ce5046626_attacker_steals_user_underlying_assets))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
