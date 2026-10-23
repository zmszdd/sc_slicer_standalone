; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca2bd2605_alice_in_active_set_after () Bool)
(declare-fun ca2bd2605_alice_in_active_set_before () Bool)
(declare-fun ca2bd2605_claimable_shares () Int)
(declare-fun ca2bd2605_pending_deposit_amount () Int)
(declare-fun ca2bd2605_pending_ignored_by_manager () Bool)
(assert
 (= ca2bd2605_alice_in_active_set_after ca2bd2605_alice_in_active_set_after))
(assert
 (= ca2bd2605_alice_in_active_set_before ca2bd2605_alice_in_active_set_before))
(assert
 (= ca2bd2605_claimable_shares ca2bd2605_claimable_shares))
(assert
 (= ca2bd2605_pending_deposit_amount ca2bd2605_pending_deposit_amount))
(assert
 (= ca2bd2605_pending_ignored_by_manager ca2bd2605_pending_ignored_by_manager))
(define-fun report_preconditions () Bool (and (= 50 ca2bd2605_pending_deposit_amount)
     (= 100 ca2bd2605_claimable_shares)
     ca2bd2605_alice_in_active_set_before))
(define-fun report_safety () Bool (=> (and (< 0 ca2bd2605_pending_deposit_amount)
         ca2bd2605_alice_in_active_set_before)
    (and ca2bd2605_alice_in_active_set_after
         (not ca2bd2605_pending_ignored_by_manager))))
(define-fun report_effects () Bool (and (< 0 ca2bd2605_pending_deposit_amount)
     ca2bd2605_alice_in_active_set_before
     (not (and ca2bd2605_alice_in_active_set_after
               (not ca2bd2605_pending_ignored_by_manager)))))
