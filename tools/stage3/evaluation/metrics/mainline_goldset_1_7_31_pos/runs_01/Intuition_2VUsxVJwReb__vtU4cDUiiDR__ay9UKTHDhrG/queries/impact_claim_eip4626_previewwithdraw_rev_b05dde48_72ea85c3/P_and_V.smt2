; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun caeef0b65_first_deposit_assets_wei () Int)
(declare-fun caeef0b65_first_deposit_shares () Int)
(declare-fun caeef0b65_offset18_initialized () Int)
(declare-fun caeef0b65_preview_assets_within_max () Bool)
(declare-fun caeef0b65_preview_withdraw_reverted () Bool)
(declare-fun caeef0b65_slope18_initialized () Int)
(assert
 (= caeef0b65_first_deposit_assets_wei caeef0b65_first_deposit_assets_wei))
(assert
 (= caeef0b65_first_deposit_shares caeef0b65_first_deposit_shares))
(assert
 (= caeef0b65_offset18_initialized caeef0b65_offset18_initialized))
(assert
 (= caeef0b65_preview_assets_within_max caeef0b65_preview_assets_within_max))
(assert
 (= caeef0b65_preview_withdraw_reverted caeef0b65_preview_withdraw_reverted))
(assert
 (= caeef0b65_slope18_initialized caeef0b65_slope18_initialized))
(define-fun report_preconditions () Bool (and (= 0 caeef0b65_offset18_initialized)
     (= 2000000000000000000 caeef0b65_slope18_initialized)
     (= 2 caeef0b65_first_deposit_assets_wei)
     (= 1414213562 caeef0b65_first_deposit_shares)
     caeef0b65_preview_assets_within_max))
(define-fun report_safety () Bool (not caeef0b65_preview_withdraw_reverted))
(define-fun report_effects () Bool (and caeef0b65_preview_assets_within_max
     caeef0b65_preview_withdraw_reverted
     caeef0b65_preview_withdraw_reverted
     caeef0b65_preview_assets_within_max))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
