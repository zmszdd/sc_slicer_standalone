; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c2e42910a_add_rewards_called_with_reentrant_token () Bool)
(declare-fun c2e42910a_reentrancy_guard_absent () Bool)
(declare-fun c2e42910a_reentrancy_window_open () Bool)
(declare-fun c2e42910a_transfer_from_completed_before_bookkeeping () Bool)
(assert
 (= c2e42910a_add_rewards_called_with_reentrant_token c2e42910a_add_rewards_called_with_reentrant_token))
(assert
 (= c2e42910a_reentrancy_guard_absent c2e42910a_reentrancy_guard_absent))
(assert
 (= c2e42910a_reentrancy_window_open c2e42910a_reentrancy_window_open))
(assert
 (= c2e42910a_transfer_from_completed_before_bookkeeping c2e42910a_transfer_from_completed_before_bookkeeping))
(define-fun report_preconditions () Bool (and c2e42910a_add_rewards_called_with_reentrant_token
     c2e42910a_reentrancy_guard_absent))
(define-fun report_safety () Bool (=> c2e42910a_reentrancy_window_open
    (=> (and c2e42910a_add_rewards_called_with_reentrant_token
             c2e42910a_reentrancy_guard_absent)
        c2e42910a_transfer_from_completed_before_bookkeeping)))
(define-fun report_effects () Bool (and c2e42910a_reentrancy_window_open
     c2e42910a_add_rewards_called_with_reentrant_token
     c2e42910a_reentrancy_guard_absent
     (not c2e42910a_transfer_from_completed_before_bookkeeping)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
