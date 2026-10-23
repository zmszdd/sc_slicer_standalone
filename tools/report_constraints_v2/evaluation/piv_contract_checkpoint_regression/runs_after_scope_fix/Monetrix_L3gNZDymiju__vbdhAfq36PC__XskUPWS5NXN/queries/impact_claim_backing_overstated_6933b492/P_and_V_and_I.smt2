; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c6069b05f_auto_borrow_occurred () Bool)
(declare-fun c6069b05f_portfolio_margin_enabled () Bool)
(declare-fun c6069b05f_real_net_assets () Int)
(declare-fun c6069b05f_reported_backing () Int)
(declare-fun c6069b05f_usdm_minted_ratio () Int)
(assert
 (= c6069b05f_auto_borrow_occurred c6069b05f_auto_borrow_occurred))
(assert
 (= c6069b05f_portfolio_margin_enabled c6069b05f_portfolio_margin_enabled))
(assert
 (= c6069b05f_real_net_assets c6069b05f_real_net_assets))
(assert
 (= c6069b05f_reported_backing c6069b05f_reported_backing))
(assert
 (= c6069b05f_usdm_minted_ratio c6069b05f_usdm_minted_ratio))
(define-fun report_preconditions () Bool (and c6069b05f_portfolio_margin_enabled
     (= 1 c6069b05f_usdm_minted_ratio)
     c6069b05f_auto_borrow_occurred))
(define-fun report_safety () Bool (=> (and c6069b05f_portfolio_margin_enabled c6069b05f_auto_borrow_occurred)
    (<= c6069b05f_reported_backing c6069b05f_real_net_assets)))
(define-fun report_effects () Bool (and c6069b05f_portfolio_margin_enabled
     c6069b05f_auto_borrow_occurred
     (not (<= c6069b05f_reported_backing c6069b05f_real_net_assets))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
