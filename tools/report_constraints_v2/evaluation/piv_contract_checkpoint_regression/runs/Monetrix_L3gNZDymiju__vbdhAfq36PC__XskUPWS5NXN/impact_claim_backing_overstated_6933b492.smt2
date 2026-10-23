; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c6069b05f_auto_borrow_active () Bool)
(declare-fun c6069b05f_portfolio_margin_enabled () Bool)
(declare-fun c6069b05f_real_net_assets () Int)
(declare-fun c6069b05f_total_backing_signed () Int)
(assert
 (= c6069b05f_auto_borrow_active c6069b05f_auto_borrow_active))
(assert
 (= c6069b05f_portfolio_margin_enabled c6069b05f_portfolio_margin_enabled))
(assert
 (= c6069b05f_real_net_assets c6069b05f_real_net_assets))
(assert
 (= c6069b05f_total_backing_signed c6069b05f_total_backing_signed))
(define-fun report_preconditions () Bool (and c6069b05f_portfolio_margin_enabled c6069b05f_auto_borrow_active))
(define-fun report_safety () Bool (=> (and c6069b05f_portfolio_margin_enabled c6069b05f_auto_borrow_active)
    (<= c6069b05f_total_backing_signed c6069b05f_real_net_assets)))
(define-fun report_effects () Bool (and c6069b05f_portfolio_margin_enabled
     c6069b05f_auto_borrow_active
     (not (<= c6069b05f_total_backing_signed c6069b05f_real_net_assets))))
