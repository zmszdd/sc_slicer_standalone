; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c4dc1f977_net_real_backing () Int)
(declare-fun c4dc1f977_pm_borrow_debt () Int)
(declare-fun c4dc1f977_pm_supplied_principal () Int)
(declare-fun c4dc1f977_reported_backing () Int)
(declare-fun c4dc1f977_usdm_undercollateralized_flag () Bool)
(assert
 (= c4dc1f977_net_real_backing c4dc1f977_net_real_backing))
(assert
 (= c4dc1f977_pm_borrow_debt c4dc1f977_pm_borrow_debt))
(assert
 (= c4dc1f977_pm_supplied_principal c4dc1f977_pm_supplied_principal))
(assert
 (= c4dc1f977_reported_backing c4dc1f977_reported_backing))
(assert
 (= c4dc1f977_usdm_undercollateralized_flag c4dc1f977_usdm_undercollateralized_flag))
(define-fun report_preconditions () Bool (and (< 0 c4dc1f977_pm_borrow_debt) (< 0 c4dc1f977_pm_supplied_principal)))
(define-fun report_safety () Bool (=> (= c4dc1f977_net_real_backing
       (- c4dc1f977_pm_supplied_principal c4dc1f977_pm_borrow_debt))
    (=> (and (< 0 c4dc1f977_pm_borrow_debt)
             (< 0 c4dc1f977_pm_supplied_principal))
        (or (<= c4dc1f977_reported_backing c4dc1f977_net_real_backing)
            (not c4dc1f977_usdm_undercollateralized_flag)))))
(define-fun report_effects () Bool (and (= c4dc1f977_net_real_backing
        (- c4dc1f977_pm_supplied_principal c4dc1f977_pm_borrow_debt))
     (< 0 c4dc1f977_pm_borrow_debt)
     (< 0 c4dc1f977_pm_supplied_principal)
     (not (or (<= c4dc1f977_reported_backing c4dc1f977_net_real_backing)
              (not c4dc1f977_usdm_undercollateralized_flag)))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
