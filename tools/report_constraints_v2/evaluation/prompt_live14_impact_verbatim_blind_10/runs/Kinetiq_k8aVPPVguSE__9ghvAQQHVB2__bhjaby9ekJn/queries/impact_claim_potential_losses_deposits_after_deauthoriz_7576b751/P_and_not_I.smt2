; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c095fcd7f_contract_authorized_before () Bool)
(declare-fun c095fcd7f_contract_deauthorized () Bool)
(declare-fun c095fcd7f_contract_paused_after_deauthorization () Bool)
(declare-fun c095fcd7f_users_can_deposit_after_deauthorization () Bool)
(assert
 (= c095fcd7f_contract_authorized_before c095fcd7f_contract_authorized_before))
(assert
 (= c095fcd7f_contract_deauthorized c095fcd7f_contract_deauthorized))
(assert
 (= c095fcd7f_contract_paused_after_deauthorization c095fcd7f_contract_paused_after_deauthorization))
(assert
 (= c095fcd7f_users_can_deposit_after_deauthorization c095fcd7f_users_can_deposit_after_deauthorization))
(define-fun report_preconditions () Bool c095fcd7f_contract_authorized_before)
(define-fun report_safety () Bool (=> (and c095fcd7f_contract_authorized_before c095fcd7f_contract_deauthorized)
    (and c095fcd7f_contract_paused_after_deauthorization
         (not c095fcd7f_users_can_deposit_after_deauthorization))))
(define-fun report_effects () Bool (and c095fcd7f_contract_authorized_before
     c095fcd7f_contract_deauthorized
     (not (and c095fcd7f_contract_paused_after_deauthorization
               (not c095fcd7f_users_can_deposit_after_deauthorization)))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
