; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbfd1d621_custodian_topup_slow () Bool)
(declare-fun cbfd1d621_fast_withdrawal_available () Bool)
(declare-fun cbfd1d621_rebalance_publicly_callable () Bool)
(declare-fun cbfd1d621_rebalance_unbounded () Bool)
(declare-fun cbfd1d621_target_balance () Int)
(declare-fun cbfd1d621_vault_balance_before_rebalance () Int)
(assert
 (= cbfd1d621_custodian_topup_slow cbfd1d621_custodian_topup_slow))
(assert
 (= cbfd1d621_fast_withdrawal_available cbfd1d621_fast_withdrawal_available))
(assert
 (= cbfd1d621_rebalance_publicly_callable cbfd1d621_rebalance_publicly_callable))
(assert
 (= cbfd1d621_rebalance_unbounded cbfd1d621_rebalance_unbounded))
(assert
 (= cbfd1d621_target_balance cbfd1d621_target_balance))
(assert
 (= cbfd1d621_vault_balance_before_rebalance cbfd1d621_vault_balance_before_rebalance))
(define-fun report_preconditions () Bool (and cbfd1d621_rebalance_publicly_callable
     cbfd1d621_rebalance_unbounded
     (> cbfd1d621_vault_balance_before_rebalance cbfd1d621_target_balance)
     cbfd1d621_custodian_topup_slow))
(define-fun report_safety () Bool (=> (and cbfd1d621_rebalance_publicly_callable
         cbfd1d621_rebalance_unbounded
         (> cbfd1d621_vault_balance_before_rebalance cbfd1d621_target_balance)
         cbfd1d621_custodian_topup_slow)
    cbfd1d621_fast_withdrawal_available))
(define-fun report_effects () Bool (and cbfd1d621_rebalance_publicly_callable
     cbfd1d621_rebalance_unbounded
     (> cbfd1d621_vault_balance_before_rebalance cbfd1d621_target_balance)
     cbfd1d621_custodian_topup_slow
     (not cbfd1d621_fast_withdrawal_available)))
