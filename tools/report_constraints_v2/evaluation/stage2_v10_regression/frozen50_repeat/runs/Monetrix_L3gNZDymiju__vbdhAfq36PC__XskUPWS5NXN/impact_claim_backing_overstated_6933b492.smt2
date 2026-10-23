; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c6069b05f_auto_borrow_occurred () Bool)
(declare-fun c6069b05f_portfolio_margin_active () Bool)
(declare-fun c6069b05f_real_backing () Int)
(declare-fun c6069b05f_reported_backing () Int)
(declare-fun c6069b05f_vault_holds_position () Bool)
(assert
 (= c6069b05f_auto_borrow_occurred c6069b05f_auto_borrow_occurred))
(assert
 (= c6069b05f_portfolio_margin_active c6069b05f_portfolio_margin_active))
(assert
 (= c6069b05f_real_backing c6069b05f_real_backing))
(assert
 (= c6069b05f_reported_backing c6069b05f_reported_backing))
(assert
 (= c6069b05f_vault_holds_position c6069b05f_vault_holds_position))
(define-fun report_preconditions () Bool (and c6069b05f_portfolio_margin_active
     c6069b05f_vault_holds_position
     c6069b05f_auto_borrow_occurred))
(define-fun report_safety () Bool (=> (and c6069b05f_portfolio_margin_active
         c6069b05f_vault_holds_position
         c6069b05f_auto_borrow_occurred)
    (<= c6069b05f_reported_backing c6069b05f_real_backing)))
(define-fun report_effects () Bool (and c6069b05f_portfolio_margin_active
     c6069b05f_vault_holds_position
     c6069b05f_auto_borrow_occurred
     (not (<= c6069b05f_reported_backing c6069b05f_real_backing))))
