; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca7a749ca_auto_borrow_occurred () Bool)
(declare-fun ca7a749ca_borrow_value () Int)
(declare-fun ca7a749ca_pm_enabled () Bool)
(declare-fun ca7a749ca_real_net_backing () Int)
(declare-fun ca7a749ca_reported_backing () Int)
(assert
 (= ca7a749ca_auto_borrow_occurred ca7a749ca_auto_borrow_occurred))
(assert
 (= ca7a749ca_borrow_value ca7a749ca_borrow_value))
(assert
 (= ca7a749ca_pm_enabled ca7a749ca_pm_enabled))
(assert
 (= ca7a749ca_real_net_backing ca7a749ca_real_net_backing))
(assert
 (= ca7a749ca_reported_backing ca7a749ca_reported_backing))
(define-fun report_preconditions () Bool (and ca7a749ca_pm_enabled ca7a749ca_auto_borrow_occurred))
(define-fun report_safety () Bool (=> (= ca7a749ca_real_net_backing
       (- ca7a749ca_reported_backing ca7a749ca_borrow_value))
    (=> (and ca7a749ca_pm_enabled ca7a749ca_auto_borrow_occurred)
        (<= ca7a749ca_reported_backing ca7a749ca_real_net_backing))))
(define-fun report_effects () Bool (and (= ca7a749ca_real_net_backing
        (- ca7a749ca_reported_backing ca7a749ca_borrow_value))
     ca7a749ca_pm_enabled
     ca7a749ca_auto_borrow_occurred
     (not (<= ca7a749ca_reported_backing ca7a749ca_real_net_backing))))
