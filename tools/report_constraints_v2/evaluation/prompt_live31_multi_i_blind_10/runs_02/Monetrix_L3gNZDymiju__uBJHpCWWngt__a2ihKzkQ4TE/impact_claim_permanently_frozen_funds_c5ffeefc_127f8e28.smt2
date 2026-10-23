; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c396a9d0d_funds_permanently_frozen () Bool)
(declare-fun c396a9d0d_total_owed_incremented () Bool)
(declare-fun c396a9d0d_usdc_funded_to_escrow () Bool)
(declare-fun c396a9d0d_usdm_refund_path_available () Bool)
(declare-fun c396a9d0d_usdm_transferred_to_vault () Bool)
(declare-fun c396a9d0d_user_blacklisted_before_claim () Bool)
(assert
 (= c396a9d0d_funds_permanently_frozen c396a9d0d_funds_permanently_frozen))
(assert
 (= c396a9d0d_total_owed_incremented c396a9d0d_total_owed_incremented))
(assert
 (= c396a9d0d_usdc_funded_to_escrow c396a9d0d_usdc_funded_to_escrow))
(assert
 (= c396a9d0d_usdm_refund_path_available c396a9d0d_usdm_refund_path_available))
(assert
 (= c396a9d0d_usdm_transferred_to_vault c396a9d0d_usdm_transferred_to_vault))
(assert
 (= c396a9d0d_user_blacklisted_before_claim c396a9d0d_user_blacklisted_before_claim))
(define-fun report_preconditions () Bool (and c396a9d0d_usdm_transferred_to_vault
     c396a9d0d_total_owed_incremented
     c396a9d0d_usdc_funded_to_escrow
     c396a9d0d_user_blacklisted_before_claim))
(define-fun report_safety () Bool (=> c396a9d0d_funds_permanently_frozen
    (=> (and c396a9d0d_usdm_transferred_to_vault
             c396a9d0d_total_owed_incremented
             c396a9d0d_usdc_funded_to_escrow
             c396a9d0d_user_blacklisted_before_claim)
        c396a9d0d_usdm_refund_path_available)))
(define-fun report_effects () Bool (and c396a9d0d_funds_permanently_frozen
     c396a9d0d_usdm_transferred_to_vault
     c396a9d0d_total_owed_incremented
     c396a9d0d_usdc_funded_to_escrow
     c396a9d0d_user_blacklisted_before_claim
     (not c396a9d0d_usdm_refund_path_available)))
