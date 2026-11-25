; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ced34a55a_real_distributable_surplus () Int)
(declare-fun ced34a55a_settle_amount () Int)
(declare-fun ced34a55a_usdc_transferred_to_yieldescrow () Int)
(declare-fun ced34a55a_vault_borrow_liability_present () Bool)
(assert
 (= ced34a55a_real_distributable_surplus ced34a55a_real_distributable_surplus))
(assert
 (= ced34a55a_settle_amount ced34a55a_settle_amount))
(assert
 (= ced34a55a_usdc_transferred_to_yieldescrow ced34a55a_usdc_transferred_to_yieldescrow))
(assert
 (= ced34a55a_vault_borrow_liability_present ced34a55a_vault_borrow_liability_present))
(define-fun report_preconditions () Bool ced34a55a_vault_borrow_liability_present)
(define-fun report_safety () Bool (=> ced34a55a_vault_borrow_liability_present
    (<= ced34a55a_settle_amount ced34a55a_real_distributable_surplus)))
(define-fun report_effects () Bool (and ced34a55a_vault_borrow_liability_present
     (not (<= ced34a55a_settle_amount ced34a55a_real_distributable_surplus))
     (< 0 ced34a55a_usdc_transferred_to_yieldescrow)))
