; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
 (declare-fun recipient () ReportAddress)
(declare-fun contract_address () ReportAddress)
(declare-fun self_transfer_noop () Bool)
(declare-fun base_supply_decremented () Bool)
(declare-fun tokens_left_contract () Bool)
(assert
 (= recipient recipient))
(assert
 (= contract_address contract_address))
(assert
 (= self_transfer_noop self_transfer_noop))
(assert
 (= base_supply_decremented base_supply_decremented))
(assert
 (= tokens_left_contract tokens_left_contract))
(define-fun report_preconditions () Bool (and (= recipient contract_address) self_transfer_noop))
(define-fun report_safety () Bool (=> (and (= recipient contract_address) self_transfer_noop)
    (or tokens_left_contract (not base_supply_decremented))))
(define-fun report_effects () Bool (and (= recipient contract_address)
     self_transfer_noop
     (not (or tokens_left_contract (not base_supply_decremented)))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
