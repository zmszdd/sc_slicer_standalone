; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd7fded92_auto_borrow_triggered () Bool)
(declare-fun cd7fded92_phantom_surplus_passes_gate () Bool)
(declare-fun cd7fded92_portfolio_margin_enabled () Bool)
(declare-fun cd7fded92_usdm_minted_ratio () Int)
(assert
 (= cd7fded92_auto_borrow_triggered cd7fded92_auto_borrow_triggered))
(assert
 (= cd7fded92_phantom_surplus_passes_gate cd7fded92_phantom_surplus_passes_gate))
(assert
 (= cd7fded92_portfolio_margin_enabled cd7fded92_portfolio_margin_enabled))
(assert
 (= cd7fded92_usdm_minted_ratio cd7fded92_usdm_minted_ratio))
(define-fun report_preconditions () Bool (and cd7fded92_portfolio_margin_enabled
     (= 1 cd7fded92_usdm_minted_ratio)
     cd7fded92_auto_borrow_triggered))
(define-fun report_safety () Bool (=> (and cd7fded92_portfolio_margin_enabled
         (= 1 cd7fded92_usdm_minted_ratio)
         cd7fded92_auto_borrow_triggered)
    (not cd7fded92_phantom_surplus_passes_gate)))
(define-fun report_effects () Bool (and cd7fded92_portfolio_margin_enabled
     (= 1 cd7fded92_usdm_minted_ratio)
     cd7fded92_auto_borrow_triggered
     (not (not cd7fded92_phantom_surplus_passes_gate))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
