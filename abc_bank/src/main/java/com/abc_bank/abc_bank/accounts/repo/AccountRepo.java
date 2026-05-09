package com.abc_bank.abc_bank.accounts.repo;

import com.abc_bank.abc_bank.accounts.entity.Account;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface AccountRepo extends JpaRepository<Account,Long> {
    Optional<Account> findByAccountNumber(String accountNumber);
    List<Account>  findByUserId(Long userId);
}
