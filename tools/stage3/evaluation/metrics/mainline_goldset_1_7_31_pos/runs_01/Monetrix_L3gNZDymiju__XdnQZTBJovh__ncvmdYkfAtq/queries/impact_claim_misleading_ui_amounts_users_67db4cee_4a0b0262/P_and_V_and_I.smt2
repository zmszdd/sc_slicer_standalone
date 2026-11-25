; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c10e8e198_misleading_ui_amounts_observed () Bool)
(declare-fun c10e8e198_susdm_decimals_expected () Int)
(declare-fun c10e8e198_susdm_decimals_offset () Int)
(declare-fun c10e8e198_susdm_decimals_reported () Int)
(declare-fun c10e8e198_usdm_asset_decimals () Int)
(assert
 (= c10e8e198_misleading_ui_amounts_observed c10e8e198_misleading_ui_amounts_observed))
(assert
 (= c10e8e198_susdm_decimals_expected c10e8e198_susdm_decimals_expected))
(assert
 (= c10e8e198_susdm_decimals_offset c10e8e198_susdm_decimals_offset))
(assert
 (= c10e8e198_susdm_decimals_reported c10e8e198_susdm_decimals_reported))
(assert
 (= c10e8e198_usdm_asset_decimals c10e8e198_usdm_asset_decimals))
(define-fun report_preconditions () Bool (and (= 6 c10e8e198_usdm_asset_decimals)
     (= 6 c10e8e198_susdm_decimals_offset)
     (= 6 c10e8e198_susdm_decimals_reported)
     c10e8e198_misleading_ui_amounts_observed))
(define-fun report_safety () Bool (=> (= c10e8e198_susdm_decimals_expected
       (+ c10e8e198_usdm_asset_decimals c10e8e198_susdm_decimals_offset))
    (= c10e8e198_susdm_decimals_reported c10e8e198_susdm_decimals_expected)))
(define-fun report_effects () Bool (and (= c10e8e198_susdm_decimals_expected
        (+ c10e8e198_usdm_asset_decimals c10e8e198_susdm_decimals_offset))
     c10e8e198_misleading_ui_amounts_observed
     (not (= c10e8e198_susdm_decimals_reported
             c10e8e198_susdm_decimals_expected))
     c10e8e198_misleading_ui_amounts_observed))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
