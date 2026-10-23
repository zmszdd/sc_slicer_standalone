; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ceeeb4fb6_funds_permanently_frozen () Bool)
(declare-fun ceeeb4fb6_total_owed_incremented () Bool)
(declare-fun ceeeb4fb6_total_owed_reduced_by_payout () Bool)
(declare-fun ceeeb4fb6_usdc_funded_to_escrow () Bool)
(declare-fun ceeeb4fb6_usdm_transferred_to_vault () Bool)
(declare-fun ceeeb4fb6_user_blacklisted () Bool)
(assert
 (= ceeeb4fb6_funds_permanently_frozen ceeeb4fb6_funds_permanently_frozen))
(assert
 (= ceeeb4fb6_total_owed_incremented ceeeb4fb6_total_owed_incremented))
(assert
 (= ceeeb4fb6_total_owed_reduced_by_payout ceeeb4fb6_total_owed_reduced_by_payout))
(assert
 (= ceeeb4fb6_usdc_funded_to_escrow ceeeb4fb6_usdc_funded_to_escrow))
(assert
 (= ceeeb4fb6_usdm_transferred_to_vault ceeeb4fb6_usdm_transferred_to_vault))
(assert
 (= ceeeb4fb6_user_blacklisted ceeeb4fb6_user_blacklisted))
(define-fun report_preconditions () Bool (and ceeeb4fb6_usdm_transferred_to_vault
     ceeeb4fb6_total_owed_incremented
     ceeeb4fb6_usdc_funded_to_escrow
     ceeeb4fb6_user_blacklisted))
(define-fun report_safety () Bool (=> ceeeb4fb6_funds_permanently_frozen
    (=> (and ceeeb4fb6_usdm_transferred_to_vault
             ceeeb4fb6_total_owed_incremented
             ceeeb4fb6_usdc_funded_to_escrow)
        ceeeb4fb6_total_owed_reduced_by_payout)))
(define-fun report_effects () Bool (and ceeeb4fb6_funds_permanently_frozen
     ceeeb4fb6_usdm_transferred_to_vault
     ceeeb4fb6_total_owed_incremented
     ceeeb4fb6_usdc_funded_to_escrow
     (not ceeeb4fb6_total_owed_reduced_by_payout)))
