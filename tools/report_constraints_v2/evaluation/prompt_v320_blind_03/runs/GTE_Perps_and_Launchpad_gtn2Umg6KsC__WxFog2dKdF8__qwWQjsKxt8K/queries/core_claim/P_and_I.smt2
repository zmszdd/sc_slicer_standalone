; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun factory_publicly_callable () Bool)
(declare-fun fee_requires_launchpad_sender () Bool)
(declare-fun mempool_observable () Bool)
(declare-fun bonding_curve_fully_sold () Bool)
(declare-fun catch_swallows_pair_exists () Bool)
(declare-fun graduation_completed () Bool)
(assert
 (= factory_publicly_callable factory_publicly_callable))
(assert
 (= fee_requires_launchpad_sender fee_requires_launchpad_sender))
(assert
 (= mempool_observable mempool_observable))
(assert
 (= bonding_curve_fully_sold bonding_curve_fully_sold))
(assert
 (= catch_swallows_pair_exists catch_swallows_pair_exists))
(assert
 (= graduation_completed graduation_completed))
(define-fun report_preconditions () Bool (and factory_publicly_callable
     fee_requires_launchpad_sender
     mempool_observable
     bonding_curve_fully_sold
     catch_swallows_pair_exists))
(define-fun report_safety () Bool (=> (and bonding_curve_fully_sold
         factory_publicly_callable
         fee_requires_launchpad_sender
         catch_swallows_pair_exists)
    graduation_completed))
(define-fun report_effects () Bool (and bonding_curve_fully_sold
     factory_publicly_callable
     fee_requires_launchpad_sender
     catch_swallows_pair_exists
     (not graduation_completed)))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
