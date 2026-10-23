; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cb3340c33_share_price_accounting_corrupted () Bool)
(declare-fun cb3340c33_total_assets_before_first_fulfilment () Int)
(declare-fun cb3340c33_withdrawal_burns_shares_for_tiny_assets () Bool)
(assert
 (= cb3340c33_share_price_accounting_corrupted cb3340c33_share_price_accounting_corrupted))
(assert
 (= cb3340c33_total_assets_before_first_fulfilment cb3340c33_total_assets_before_first_fulfilment))
(assert
 (= cb3340c33_withdrawal_burns_shares_for_tiny_assets cb3340c33_withdrawal_burns_shares_for_tiny_assets))
(define-fun report_preconditions () Bool (= 1 cb3340c33_total_assets_before_first_fulfilment))
(define-fun report_safety () Bool (=> cb3340c33_withdrawal_burns_shares_for_tiny_assets
    (=> cb3340c33_withdrawal_burns_shares_for_tiny_assets
        (not cb3340c33_share_price_accounting_corrupted))))
(define-fun report_effects () Bool (and cb3340c33_withdrawal_burns_shares_for_tiny_assets
     cb3340c33_withdrawal_burns_shares_for_tiny_assets
     (not (not cb3340c33_share_price_accounting_corrupted))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
