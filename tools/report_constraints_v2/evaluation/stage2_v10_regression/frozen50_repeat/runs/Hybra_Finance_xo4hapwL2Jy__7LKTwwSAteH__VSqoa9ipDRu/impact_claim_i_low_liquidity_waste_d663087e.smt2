; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c473d8939_emissions_preserved_or_accrued () Bool)
(declare-fun c473d8939_empty_period_elapsed () Bool)
(declare-fun c473d8939_low_liquidity_waste_occurs () Bool)
(declare-fun c473d8939_notify_reward_called () Bool)
(declare-fun c473d8939_total_supply () Int)
(assert
 (= c473d8939_emissions_preserved_or_accrued c473d8939_emissions_preserved_or_accrued))
(assert
 (= c473d8939_empty_period_elapsed c473d8939_empty_period_elapsed))
(assert
 (= c473d8939_low_liquidity_waste_occurs c473d8939_low_liquidity_waste_occurs))
(assert
 (= c473d8939_notify_reward_called c473d8939_notify_reward_called))
(assert
 (= c473d8939_total_supply c473d8939_total_supply))
(define-fun report_preconditions () Bool (and (= 0 c473d8939_total_supply)
     c473d8939_empty_period_elapsed
     c473d8939_notify_reward_called))
(define-fun report_safety () Bool (=> (and (= 0 c473d8939_total_supply)
         c473d8939_empty_period_elapsed
         c473d8939_notify_reward_called)
    (and c473d8939_emissions_preserved_or_accrued
         (not c473d8939_low_liquidity_waste_occurs))))
(define-fun report_effects () Bool (and (= 0 c473d8939_total_supply)
     c473d8939_empty_period_elapsed
     c473d8939_notify_reward_called
     (not (and c473d8939_emissions_preserved_or_accrued
               (not c473d8939_low_liquidity_waste_occurs)))))
