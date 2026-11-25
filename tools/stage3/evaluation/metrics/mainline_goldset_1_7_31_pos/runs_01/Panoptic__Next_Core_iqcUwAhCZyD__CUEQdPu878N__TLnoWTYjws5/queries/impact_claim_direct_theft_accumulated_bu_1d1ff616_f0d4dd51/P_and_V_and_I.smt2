; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c132b4792_admin_change_call () Bool)
(declare-fun c132b4792_all_accumulated_fees_stolen () Bool)
(declare-fun c132b4792_builder_admin_set_at_deploy () Bool)
(declare-fun c132b4792_caller_is_current_admin () Bool)
(declare-fun c132b4792_fees_accumulated_in_wallet () Bool)
(assert
 (= c132b4792_admin_change_call c132b4792_admin_change_call))
(assert
 (= c132b4792_all_accumulated_fees_stolen c132b4792_all_accumulated_fees_stolen))
(assert
 (= c132b4792_builder_admin_set_at_deploy c132b4792_builder_admin_set_at_deploy))
(assert
 (= c132b4792_caller_is_current_admin c132b4792_caller_is_current_admin))
(assert
 (= c132b4792_fees_accumulated_in_wallet c132b4792_fees_accumulated_in_wallet))
(define-fun report_preconditions () Bool (and c132b4792_builder_admin_set_at_deploy c132b4792_fees_accumulated_in_wallet))
(define-fun report_safety () Bool (=> c132b4792_admin_change_call c132b4792_caller_is_current_admin))
(define-fun report_effects () Bool (and c132b4792_admin_change_call
     (not c132b4792_caller_is_current_admin)
     c132b4792_all_accumulated_fees_stolen
     c132b4792_all_accumulated_fees_stolen))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
