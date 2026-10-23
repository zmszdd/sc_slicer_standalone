; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
 (declare-fun c2621705f_accounted_balance_after_redeem () Int)
(declare-fun c2621705f_attacker_deposit_eth () Int)
(declare-fun c2621705f_covenant_contract_address () ReportAddress)
(declare-fun c2621705f_physical_balance_after_redeem () Int)
(declare-fun c2621705f_recipient_is_contract_contract () ReportAddress)
(assert
 (= c2621705f_accounted_balance_after_redeem c2621705f_accounted_balance_after_redeem))
(assert
 (= c2621705f_attacker_deposit_eth c2621705f_attacker_deposit_eth))
(assert
 (= c2621705f_covenant_contract_address c2621705f_covenant_contract_address))
(assert
 (= c2621705f_physical_balance_after_redeem c2621705f_physical_balance_after_redeem))
(assert
 (= c2621705f_recipient_is_contract_contract c2621705f_recipient_is_contract_contract))
(define-fun report_preconditions () Bool (and (= c2621705f_recipient_is_contract_contract
        c2621705f_covenant_contract_address)
     (= 100 c2621705f_attacker_deposit_eth)))
(define-fun report_safety () Bool (=> (and (= c2621705f_recipient_is_contract_contract
            c2621705f_covenant_contract_address)
         (= 100 c2621705f_attacker_deposit_eth))
    (>= c2621705f_physical_balance_after_redeem
        c2621705f_accounted_balance_after_redeem)))
(define-fun report_effects () Bool (and (= c2621705f_recipient_is_contract_contract
        c2621705f_covenant_contract_address)
     (= 100 c2621705f_attacker_deposit_eth)
     (not (>= c2621705f_physical_balance_after_redeem
              c2621705f_accounted_balance_after_redeem))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
