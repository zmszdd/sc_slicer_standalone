; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd77ae92c_dynamic_fee_accepted () Bool)
(declare-fun cd77ae92c_dynamic_fee_mechanism_ineffective () Bool)
(declare-fun cd77ae92c_max_fee_cap () Int)
(assert
 (= cd77ae92c_dynamic_fee_accepted cd77ae92c_dynamic_fee_accepted))
(assert
 (= cd77ae92c_dynamic_fee_mechanism_ineffective cd77ae92c_dynamic_fee_mechanism_ineffective))
(assert
 (= cd77ae92c_max_fee_cap cd77ae92c_max_fee_cap))
(define-fun report_preconditions () Bool (= 500000 cd77ae92c_max_fee_cap))
(define-fun report_safety () Bool (=> cd77ae92c_dynamic_fee_mechanism_ineffective
    (=> (= 500000 cd77ae92c_max_fee_cap) cd77ae92c_dynamic_fee_accepted)))
(define-fun report_effects () Bool (and cd77ae92c_dynamic_fee_mechanism_ineffective
     (= 500000 cd77ae92c_max_fee_cap)
     (not cd77ae92c_dynamic_fee_accepted)))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
