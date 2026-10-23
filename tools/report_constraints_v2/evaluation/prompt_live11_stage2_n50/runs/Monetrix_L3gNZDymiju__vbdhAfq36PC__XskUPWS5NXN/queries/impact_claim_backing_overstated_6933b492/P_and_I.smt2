; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c6069b05f_auto_borrow_occurred () Bool)
(declare-fun c6069b05f_borrow_value () Int)
(declare-fun c6069b05f_pm_enabled () Bool)
(declare-fun c6069b05f_real_net_assets () Int)
(declare-fun c6069b05f_reported_backing () Int)
(declare-fun c6069b05f_summed_supply () Int)
(declare-fun c6069b05f_vault_has_l1_position () Bool)
(assert
 (= c6069b05f_auto_borrow_occurred c6069b05f_auto_borrow_occurred))
(assert
 (= c6069b05f_borrow_value c6069b05f_borrow_value))
(assert
 (= c6069b05f_pm_enabled c6069b05f_pm_enabled))
(assert
 (= c6069b05f_real_net_assets c6069b05f_real_net_assets))
(assert
 (= c6069b05f_reported_backing c6069b05f_reported_backing))
(assert
 (= c6069b05f_summed_supply c6069b05f_summed_supply))
(assert
 (= c6069b05f_vault_has_l1_position c6069b05f_vault_has_l1_position))
(define-fun report_preconditions () Bool (and c6069b05f_pm_enabled
     c6069b05f_vault_has_l1_position
     c6069b05f_auto_borrow_occurred))
(define-fun report_safety () Bool (=> (= c6069b05f_real_net_assets
       (- c6069b05f_summed_supply c6069b05f_borrow_value))
    (=> (and c6069b05f_pm_enabled
             c6069b05f_vault_has_l1_position
             c6069b05f_auto_borrow_occurred)
        (<= c6069b05f_reported_backing c6069b05f_real_net_assets))))
(define-fun report_effects () Bool (and (= c6069b05f_real_net_assets
        (- c6069b05f_summed_supply c6069b05f_borrow_value))
     c6069b05f_pm_enabled
     c6069b05f_vault_has_l1_position
     c6069b05f_auto_borrow_occurred
     (not (<= c6069b05f_reported_backing c6069b05f_real_net_assets))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
