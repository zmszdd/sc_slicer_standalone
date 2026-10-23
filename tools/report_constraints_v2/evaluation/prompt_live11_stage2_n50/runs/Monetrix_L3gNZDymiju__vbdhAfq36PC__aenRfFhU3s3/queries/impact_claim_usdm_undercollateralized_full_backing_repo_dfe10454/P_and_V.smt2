; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c0bf8d8ae_borrow_debt_exists () Bool)
(declare-fun c0bf8d8ae_principal_bridged () Bool)
(declare-fun c0bf8d8ae_reported_full_backing () Bool)
(declare-fun c0bf8d8ae_usdm_deposited () Bool)
(declare-fun c0bf8d8ae_usdm_undercollateralized () Bool)
(assert
 (= c0bf8d8ae_borrow_debt_exists c0bf8d8ae_borrow_debt_exists))
(assert
 (= c0bf8d8ae_principal_bridged c0bf8d8ae_principal_bridged))
(assert
 (= c0bf8d8ae_reported_full_backing c0bf8d8ae_reported_full_backing))
(assert
 (= c0bf8d8ae_usdm_deposited c0bf8d8ae_usdm_deposited))
(assert
 (= c0bf8d8ae_usdm_undercollateralized c0bf8d8ae_usdm_undercollateralized))
(define-fun report_preconditions () Bool (and c0bf8d8ae_usdm_deposited
     c0bf8d8ae_principal_bridged
     c0bf8d8ae_borrow_debt_exists))
(define-fun report_safety () Bool (=> (and c0bf8d8ae_usdm_deposited
         c0bf8d8ae_principal_bridged
         c0bf8d8ae_borrow_debt_exists)
    (and (not c0bf8d8ae_reported_full_backing)
         (not c0bf8d8ae_usdm_undercollateralized))))
(define-fun report_effects () Bool (and c0bf8d8ae_usdm_deposited
     c0bf8d8ae_principal_bridged
     c0bf8d8ae_borrow_debt_exists
     (not (and (not c0bf8d8ae_reported_full_backing)
               (not c0bf8d8ae_usdm_undercollateralized)))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
