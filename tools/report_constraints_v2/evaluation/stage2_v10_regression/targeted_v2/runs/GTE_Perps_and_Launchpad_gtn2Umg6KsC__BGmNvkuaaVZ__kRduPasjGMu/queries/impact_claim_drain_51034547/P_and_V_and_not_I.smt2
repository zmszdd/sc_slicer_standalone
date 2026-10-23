; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd9f65f93_balance_reserve_consistent () Bool)
(declare-fun cd9f65f93_pair_drained () Bool)
(declare-fun cd9f65f93_time_elapsed () Int)
(declare-fun cd9f65f93_total_launchpad_fees_nonzero () Bool)
(assert
 (= cd9f65f93_balance_reserve_consistent cd9f65f93_balance_reserve_consistent))
(assert
 (= cd9f65f93_pair_drained cd9f65f93_pair_drained))
(assert
 (= cd9f65f93_time_elapsed cd9f65f93_time_elapsed))
(assert
 (= cd9f65f93_total_launchpad_fees_nonzero cd9f65f93_total_launchpad_fees_nonzero))
(define-fun report_preconditions () Bool (and cd9f65f93_total_launchpad_fees_nonzero (= 0 cd9f65f93_time_elapsed)))
(define-fun report_safety () Bool (=> (and cd9f65f93_total_launchpad_fees_nonzero (= 0 cd9f65f93_time_elapsed))
    (or cd9f65f93_balance_reserve_consistent (not cd9f65f93_pair_drained))))
(define-fun report_effects () Bool (and cd9f65f93_total_launchpad_fees_nonzero
     (= 0 cd9f65f93_time_elapsed)
     (not (or cd9f65f93_balance_reserve_consistent (not cd9f65f93_pair_drained)))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
