; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cb9952ae3_deposit_mint_failed () Bool)
(declare-fun cb9952ae3_susdm_decimals_expected () Int)
(declare-fun cb9952ae3_susdm_decimals_offset () Int)
(declare-fun cb9952ae3_susdm_decimals_reported () Int)
(declare-fun cb9952ae3_usdm_asset_decimals () Int)
(assert
 (= cb9952ae3_deposit_mint_failed cb9952ae3_deposit_mint_failed))
(assert
 (= cb9952ae3_susdm_decimals_expected cb9952ae3_susdm_decimals_expected))
(assert
 (= cb9952ae3_susdm_decimals_offset cb9952ae3_susdm_decimals_offset))
(assert
 (= cb9952ae3_susdm_decimals_reported cb9952ae3_susdm_decimals_reported))
(assert
 (= cb9952ae3_usdm_asset_decimals cb9952ae3_usdm_asset_decimals))
(define-fun report_preconditions () Bool (and (= 6 cb9952ae3_usdm_asset_decimals)
     (= 6 cb9952ae3_susdm_decimals_offset)
     (= 6 cb9952ae3_susdm_decimals_reported)))
(define-fun report_safety () Bool (=> (= cb9952ae3_susdm_decimals_expected
       (+ cb9952ae3_usdm_asset_decimals cb9952ae3_susdm_decimals_offset))
    (=> (= 6 cb9952ae3_susdm_decimals_reported)
        (= cb9952ae3_susdm_decimals_reported cb9952ae3_susdm_decimals_expected))))
(define-fun report_effects () Bool (and (= cb9952ae3_susdm_decimals_expected
        (+ cb9952ae3_usdm_asset_decimals cb9952ae3_susdm_decimals_offset))
     (= 6 cb9952ae3_susdm_decimals_reported)
     (not (= cb9952ae3_susdm_decimals_reported
             cb9952ae3_susdm_decimals_expected))
     cb9952ae3_deposit_mint_failed))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
