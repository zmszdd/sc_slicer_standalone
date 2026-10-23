; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca5277018_payout_reduces_total_owed () Bool)
(declare-fun ca5277018_payout_reverts () Bool)
(declare-fun ca5277018_total_owed_incremented () Bool)
(declare-fun ca5277018_total_owed_never_decreases_observed () Bool)
(declare-fun ca5277018_usdc_funded_to_escrow () Bool)
(declare-fun ca5277018_usdm_transferred_to_vault () Bool)
(declare-fun ca5277018_user_blacklisted () Bool)
(assert
 (= ca5277018_payout_reduces_total_owed ca5277018_payout_reduces_total_owed))
(assert
 (= ca5277018_payout_reverts ca5277018_payout_reverts))
(assert
 (= ca5277018_total_owed_incremented ca5277018_total_owed_incremented))
(assert
 (= ca5277018_total_owed_never_decreases_observed ca5277018_total_owed_never_decreases_observed))
(assert
 (= ca5277018_usdc_funded_to_escrow ca5277018_usdc_funded_to_escrow))
(assert
 (= ca5277018_usdm_transferred_to_vault ca5277018_usdm_transferred_to_vault))
(assert
 (= ca5277018_user_blacklisted ca5277018_user_blacklisted))
(define-fun report_preconditions () Bool (and ca5277018_usdm_transferred_to_vault
     ca5277018_total_owed_incremented
     ca5277018_usdc_funded_to_escrow
     ca5277018_user_blacklisted))
(define-fun report_safety () Bool (=> (and ca5277018_payout_reverts ca5277018_total_owed_never_decreases_observed)
    (=> (and ca5277018_usdm_transferred_to_vault
             ca5277018_total_owed_incremented
             ca5277018_usdc_funded_to_escrow)
        ca5277018_payout_reduces_total_owed)))
(define-fun report_effects () Bool (and ca5277018_payout_reverts
     ca5277018_total_owed_never_decreases_observed
     ca5277018_usdm_transferred_to_vault
     ca5277018_total_owed_incremented
     ca5277018_usdc_funded_to_escrow
     (not ca5277018_payout_reduces_total_owed)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
