; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbec9afe2_gauge_manager_balance_after () Int)
(declare-fun cbec9afe2_gauge_manager_balance_before () Int)
(declare-fun cbec9afe2_notified_emission_recoverable () Bool)
(declare-fun cbec9afe2_notified_emission_tracked () Bool)
(declare-fun cbec9afe2_voter_total_weight () Int)
(assert
 (= cbec9afe2_gauge_manager_balance_after cbec9afe2_gauge_manager_balance_after))
(assert
 (= cbec9afe2_gauge_manager_balance_before cbec9afe2_gauge_manager_balance_before))
(assert
 (= cbec9afe2_notified_emission_recoverable cbec9afe2_notified_emission_recoverable))
(assert
 (= cbec9afe2_notified_emission_tracked cbec9afe2_notified_emission_tracked))
(assert
 (= cbec9afe2_voter_total_weight cbec9afe2_voter_total_weight))
(define-fun report_preconditions () Bool (= 0 cbec9afe2_voter_total_weight))
(define-fun report_safety () Bool (=> (= 0 cbec9afe2_voter_total_weight)
    (= cbec9afe2_notified_emission_tracked
       cbec9afe2_notified_emission_recoverable)))
(define-fun report_effects () Bool (and (= 0 cbec9afe2_voter_total_weight)
     (not (= cbec9afe2_notified_emission_tracked
             cbec9afe2_notified_emission_recoverable))
     (>= cbec9afe2_gauge_manager_balance_after
         cbec9afe2_gauge_manager_balance_before)
     (>= cbec9afe2_gauge_manager_balance_after
         cbec9afe2_gauge_manager_balance_before)))
(assert report_preconditions)
(check-sat)
(get-model)
