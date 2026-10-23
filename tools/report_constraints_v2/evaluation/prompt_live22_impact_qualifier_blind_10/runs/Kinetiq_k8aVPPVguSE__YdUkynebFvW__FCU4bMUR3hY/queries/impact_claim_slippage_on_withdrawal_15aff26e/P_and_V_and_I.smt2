; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce46361d9_exchange_rate_slashing_dependent () Bool)
(declare-fun ce46361d9_hype_received_meets_user_minimum () Bool)
(declare-fun ce46361d9_khype_shares_provided () Int)
(declare-fun ce46361d9_slashing_reported_before_queue_tx_occurred () Bool)
(declare-fun ce46361d9_user_can_enforce_min_hype_bound () Bool)
(assert
 (= ce46361d9_exchange_rate_slashing_dependent ce46361d9_exchange_rate_slashing_dependent))
(assert
 (= ce46361d9_hype_received_meets_user_minimum ce46361d9_hype_received_meets_user_minimum))
(assert
 (= ce46361d9_khype_shares_provided ce46361d9_khype_shares_provided))
(assert
 (= ce46361d9_slashing_reported_before_queue_tx_occurred ce46361d9_slashing_reported_before_queue_tx_occurred))
(assert
 (= ce46361d9_user_can_enforce_min_hype_bound ce46361d9_user_can_enforce_min_hype_bound))
(define-fun report_preconditions () Bool (and (< 0 ce46361d9_khype_shares_provided)
     ce46361d9_exchange_rate_slashing_dependent
     ce46361d9_slashing_reported_before_queue_tx_occurred))
(define-fun report_safety () Bool (=> (not ce46361d9_hype_received_meets_user_minimum)
    (=> ce46361d9_user_can_enforce_min_hype_bound
        ce46361d9_hype_received_meets_user_minimum)))
(define-fun report_effects () Bool (and (not ce46361d9_hype_received_meets_user_minimum)
     ce46361d9_user_can_enforce_min_hype_bound
     (not ce46361d9_hype_received_meets_user_minimum)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
