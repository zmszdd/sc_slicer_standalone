; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbeb25399_epoch_timestamp_end_n () Int)
(declare-fun cbeb25399_locked_end () Int)
(declare-fun cbeb25399_user_bonded_epoch_n () Bool)
(declare-fun cbeb25399_user_epoch_n_reward_received () Int)
(declare-fun cbeb25399_user_epoch_n_reward_share () Int)
(assert
 (= cbeb25399_epoch_timestamp_end_n cbeb25399_epoch_timestamp_end_n))
(assert
 (= cbeb25399_locked_end cbeb25399_locked_end))
(assert
 (= cbeb25399_user_bonded_epoch_n cbeb25399_user_bonded_epoch_n))
(assert
 (= cbeb25399_user_epoch_n_reward_received cbeb25399_user_epoch_n_reward_received))
(assert
 (= cbeb25399_user_epoch_n_reward_share cbeb25399_user_epoch_n_reward_share))
(define-fun report_preconditions () Bool (and (<= cbeb25399_locked_end cbeb25399_epoch_timestamp_end_n)
     cbeb25399_user_bonded_epoch_n))
(define-fun report_safety () Bool (=> cbeb25399_user_bonded_epoch_n
    (>= cbeb25399_user_epoch_n_reward_received
        cbeb25399_user_epoch_n_reward_share)))
(define-fun report_effects () Bool (and cbeb25399_user_bonded_epoch_n
     (not (>= cbeb25399_user_epoch_n_reward_received
              cbeb25399_user_epoch_n_reward_share))
     (= 0 cbeb25399_user_epoch_n_reward_received)))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
