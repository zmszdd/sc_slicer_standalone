; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cceea0077_stuck_obligation_remains_in_total_owed () Bool)
(declare-fun cceea0077_total_owed_incremented () Bool)
(declare-fun cceea0077_total_owed_reduced_by_payout () Bool)
(declare-fun cceea0077_usdc_funded_to_escrow () Bool)
(declare-fun cceea0077_usdm_transferred_to_vault () Bool)
(declare-fun cceea0077_user_blacklisted () Bool)
(assert
 (= cceea0077_stuck_obligation_remains_in_total_owed cceea0077_stuck_obligation_remains_in_total_owed))
(assert
 (= cceea0077_total_owed_incremented cceea0077_total_owed_incremented))
(assert
 (= cceea0077_total_owed_reduced_by_payout cceea0077_total_owed_reduced_by_payout))
(assert
 (= cceea0077_usdc_funded_to_escrow cceea0077_usdc_funded_to_escrow))
(assert
 (= cceea0077_usdm_transferred_to_vault cceea0077_usdm_transferred_to_vault))
(assert
 (= cceea0077_user_blacklisted cceea0077_user_blacklisted))
(define-fun report_preconditions () Bool (and cceea0077_usdm_transferred_to_vault
     cceea0077_total_owed_incremented
     cceea0077_usdc_funded_to_escrow
     cceea0077_user_blacklisted))
(define-fun report_safety () Bool (=> cceea0077_stuck_obligation_remains_in_total_owed
    (=> (and cceea0077_usdm_transferred_to_vault
             cceea0077_total_owed_incremented
             cceea0077_usdc_funded_to_escrow
             cceea0077_user_blacklisted)
        cceea0077_total_owed_reduced_by_payout)))
(define-fun report_effects () Bool (and cceea0077_stuck_obligation_remains_in_total_owed
     cceea0077_usdm_transferred_to_vault
     cceea0077_total_owed_incremented
     cceea0077_usdc_funded_to_escrow
     cceea0077_user_blacklisted
     (not cceea0077_total_owed_reduced_by_payout)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
