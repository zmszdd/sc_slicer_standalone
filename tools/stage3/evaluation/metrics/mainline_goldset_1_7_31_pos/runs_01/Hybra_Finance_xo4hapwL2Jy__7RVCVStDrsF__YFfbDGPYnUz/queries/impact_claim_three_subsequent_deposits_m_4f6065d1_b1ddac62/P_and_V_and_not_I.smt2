; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c07f8692a_deposit_amount () Int)
(declare-fun c07f8692a_minted_shares_first_subsequent_deposit () Int)
(declare-fun c07f8692a_minted_shares_second_subsequent_deposit () Int)
(declare-fun c07f8692a_minted_shares_third_subsequent_deposit () Int)
(declare-fun c07f8692a_total_assets_before_deposit () Int)
(declare-fun c07f8692a_total_assets_used_for_shares () Int)
(declare-fun c07f8692a_total_supply_before_deposit () Int)
(declare-fun c07f8692a_zero_shares () Int)
(assert
 (= c07f8692a_deposit_amount c07f8692a_deposit_amount))
(assert
 (= c07f8692a_minted_shares_first_subsequent_deposit c07f8692a_minted_shares_first_subsequent_deposit))
(assert
 (= c07f8692a_minted_shares_second_subsequent_deposit c07f8692a_minted_shares_second_subsequent_deposit))
(assert
 (= c07f8692a_minted_shares_third_subsequent_deposit c07f8692a_minted_shares_third_subsequent_deposit))
(assert
 (= c07f8692a_total_assets_before_deposit c07f8692a_total_assets_before_deposit))
(assert
 (= c07f8692a_total_assets_used_for_shares c07f8692a_total_assets_used_for_shares))
(assert
 (= c07f8692a_total_supply_before_deposit c07f8692a_total_supply_before_deposit))
(assert
 (= c07f8692a_zero_shares c07f8692a_zero_shares))
(define-fun report_preconditions () Bool (and (= 1 c07f8692a_total_supply_before_deposit)
     (= 1 c07f8692a_total_assets_before_deposit)
     (< 0 c07f8692a_deposit_amount)))
(define-fun report_safety () Bool (=> (< 0 c07f8692a_deposit_amount)
    (= c07f8692a_total_assets_used_for_shares
       c07f8692a_total_assets_before_deposit)))
(define-fun report_effects () Bool (let ((a!1 (and (= c07f8692a_minted_shares_first_subsequent_deposit
                   c07f8692a_zero_shares)
                (= c07f8692a_minted_shares_second_subsequent_deposit
                   c07f8692a_zero_shares)
                (= c07f8692a_minted_shares_third_subsequent_deposit
                   c07f8692a_zero_shares))))
  (and (< 0 c07f8692a_deposit_amount)
       (not (= c07f8692a_total_assets_used_for_shares
               c07f8692a_total_assets_before_deposit))
       a!1
       a!1)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
