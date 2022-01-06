# social-nft
Community project to create a NFT

# Purpose
The idea is to "vote" for a 64px x 64px Image-NFT together made out of 37 tiles. Each period you have the chance insert your tile into the NFT. To verfiy your vote, it is required to send a transaction to this ETH-address with your specified amount in ETH. At the end of each period, the submitted tile with the biggest amount will be added to the NFT. Once all tiles are voted, an NFT will be created and auctioned on opensea.io or a similar plattform. The link will be provided on this website.

## Working Principal
The submitted user-votes are stored in a database, marked as unverfied.
Every x hours (currently once per hour) all recorded transactions to the [NFT-ETH-address](https://etherscan.io/address/0x703091392E1BEa715d9F93DaB57DAfA8bB0f45bF) are checked and stored in a database. In the next step the votes and transactions are matched based on address & amount and are flaged. 
At the end of the period (actually 6 hours after the voting-deadline) the vote/transaction, which is valid and has the highest amount, will be used to fill the tile of the current epoch. After this step, the next period is opened for voting.

Live-version is deployed [on here](https://social-nft.web.app/)
