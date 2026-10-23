; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbd13eacf_total_supply () Int)
(declare-fun cbd13eacf_unowned_shares () Int)
(declare-fun cbd13eacf_users_lose_66_percent_observed () Bool)
(assert
 (= cbd13eacf_total_supply cbd13eacf_total_supply))
(assert
 (= cbd13eacf_unowned_shares cbd13eacf_unowned_shares))
(assert
 (= cbd13eacf_users_lose_66_percent_observed cbd13eacf_users_lose_66_percent_observed))
(define-fun report_preconditions () Bool (and (= 1000000 cbd13eacf_total_supply) (< 0 cbd13eacf_unowned_shares)))
(define-fun report_safety () Bool (=> (and (= 1000000 cbd13eacf_total_supply) (< 0 cbd13eacf_unowned_shares))
    (not cbd13eacf_users_lose_66_percent_observed)))
(define-fun report_effects () Bool (and (= 1000000 cbd13eacf_total_supply)
     (< 0 cbd13eacf_unowned_shares)
     (not (not cbd13eacf_users_lose_66_percent_observed))))
(assert report_preconditions)
(check-sat)
(get-model)
