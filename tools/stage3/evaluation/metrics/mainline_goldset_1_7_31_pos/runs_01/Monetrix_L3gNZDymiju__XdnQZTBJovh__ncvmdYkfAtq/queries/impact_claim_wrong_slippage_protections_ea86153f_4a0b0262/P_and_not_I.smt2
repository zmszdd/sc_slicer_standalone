; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c5b377edf_susdm_decimals_expected () Int)
(declare-fun c5b377edf_susdm_decimals_offset () Int)
(declare-fun c5b377edf_susdm_decimals_reported () Int)
(declare-fun c5b377edf_usdm_asset_decimals () Int)
(declare-fun c5b377edf_wrong_slippage_protections_observed () Bool)
(assert
 (= c5b377edf_susdm_decimals_expected c5b377edf_susdm_decimals_expected))
(assert
 (= c5b377edf_susdm_decimals_offset c5b377edf_susdm_decimals_offset))
(assert
 (= c5b377edf_susdm_decimals_reported c5b377edf_susdm_decimals_reported))
(assert
 (= c5b377edf_usdm_asset_decimals c5b377edf_usdm_asset_decimals))
(assert
 (= c5b377edf_wrong_slippage_protections_observed c5b377edf_wrong_slippage_protections_observed))
(define-fun report_preconditions () Bool (and (= 6 c5b377edf_usdm_asset_decimals)
     (= 6 c5b377edf_susdm_decimals_offset)
     (= 6 c5b377edf_susdm_decimals_reported)))
(define-fun report_safety () Bool (=> (= c5b377edf_susdm_decimals_expected
       (+ c5b377edf_usdm_asset_decimals c5b377edf_susdm_decimals_offset))
    (=> (= 6 c5b377edf_susdm_decimals_reported)
        (= c5b377edf_susdm_decimals_reported c5b377edf_susdm_decimals_expected))))
(define-fun report_effects () Bool (and (= c5b377edf_susdm_decimals_expected
        (+ c5b377edf_usdm_asset_decimals c5b377edf_susdm_decimals_offset))
     (= 6 c5b377edf_susdm_decimals_reported)
     (not (= c5b377edf_susdm_decimals_reported
             c5b377edf_susdm_decimals_expected))
     c5b377edf_wrong_slippage_protections_observed
     c5b377edf_wrong_slippage_protections_observed))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
