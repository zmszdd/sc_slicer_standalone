; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c6957cda5_attacker_no_loss_repeatable () Bool)
(declare-fun c6957cda5_queue_loop_bounded () Bool)
(declare-fun c6957cda5_spam_requests_one_share_occurred () Bool)
(declare-fun c6957cda5_user_can_queue_arbitrary_withdrawals_occurred () Bool)
(declare-fun c6957cda5_withdrawals_prevented_by_dos () Bool)
(assert
 (= c6957cda5_attacker_no_loss_repeatable c6957cda5_attacker_no_loss_repeatable))
(assert
 (= c6957cda5_queue_loop_bounded c6957cda5_queue_loop_bounded))
(assert
 (= c6957cda5_spam_requests_one_share_occurred c6957cda5_spam_requests_one_share_occurred))
(assert
 (= c6957cda5_user_can_queue_arbitrary_withdrawals_occurred c6957cda5_user_can_queue_arbitrary_withdrawals_occurred))
(assert
 (= c6957cda5_withdrawals_prevented_by_dos c6957cda5_withdrawals_prevented_by_dos))
(define-fun report_preconditions () Bool (and c6957cda5_user_can_queue_arbitrary_withdrawals_occurred
     c6957cda5_spam_requests_one_share_occurred
     c6957cda5_attacker_no_loss_repeatable))
(define-fun report_safety () Bool (=> c6957cda5_user_can_queue_arbitrary_withdrawals_occurred
    c6957cda5_queue_loop_bounded))
(define-fun report_effects () Bool (and c6957cda5_user_can_queue_arbitrary_withdrawals_occurred
     (not c6957cda5_queue_loop_bounded)
     c6957cda5_withdrawals_prevented_by_dos))
